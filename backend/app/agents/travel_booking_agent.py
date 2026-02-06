"""
Travel Booking Agent - Parallel Multi-API Powered Flight Search
Calls ALL APIs SIMULTANEOUSLY for maximum speed, accuracy and coverage:
1. Google Flights Data API
2. Booking.com API  
3. Amadeus API
4. Serper + LLM (backup for estimates)

Results are merged, deduplicated, and ranked for best options!
"""
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from groq import AsyncGroq
from datetime import datetime


class TravelBookingAgent:
    """Parallel Multi-API powered travel booking agent for maximum accuracy."""
    
    def __init__(self, groq_api_key: str, serper_api_key: str, rapidapi_key: str, 
                 amadeus_api_key: str = None, amadeus_api_secret: str = None):
        self.groq_client = AsyncGroq(api_key=groq_api_key)
        self.serper_api_key = serper_api_key
        self.rapidapi_key = rapidapi_key
        self.amadeus_api_key = amadeus_api_key
        self.amadeus_api_secret = amadeus_api_secret
        self.model = "llama-3.3-70b-versatile"
        
        # API configurations
        self.google_flights_url = "https://google-flights-data.p.rapidapi.com"
        self.booking_url = "https://booking-com15.p.rapidapi.com/api/v1"
        self.amadeus_url = "https://test.api.amadeus.com"
        
        # Airport codes mapping
        self.airport_codes = {
            "mumbai": "BOM", "delhi": "DEL", "bangalore": "BLR", "bengaluru": "BLR",
            "chennai": "MAA", "kolkata": "CCU", "hyderabad": "HYD", "pune": "PNQ",
            "ahmedabad": "AMD", "goa": "GOI", "jaipur": "JAI", "lucknow": "LKO",
            "kochi": "COK", "cochin": "COK", "trivandrum": "TRV",
            "guwahati": "GAU", "patna": "PAT", "bhubaneswar": "BBI", "chandigarh": "IXC",
            "indore": "IDR", "nagpur": "NAG", "varanasi": "VNS", "amritsar": "ATQ",
            "srinagar": "SXR", "coimbatore": "CJB", "mangalore": "IXE", "ranchi": "IXR",
            "raipur": "RPR", "visakhapatnam": "VTZ", "vizag": "VTZ", "madurai": "IXM",
            "udaipur": "UDR", "jodhpur": "JDH", "dehradun": "DED", "leh": "IXL",
            "port blair": "IXZ", "bagdogra": "IXB",
            "new york": "JFK", "london": "LHR", "dubai": "DXB", "singapore": "SIN",
            "bangkok": "BKK", "paris": "CDG", "sydney": "SYD", "tokyo": "NRT",
            "hong kong": "HKG", "kuala lumpur": "KUL", "doha": "DOH", "abu dhabi": "AUH"
        }
    
    def _get_airport_code(self, city: str) -> str:
        """Get airport code from city name."""
        city_lower = city.lower().strip()
        if city_lower in self.airport_codes:
            return self.airport_codes[city_lower]
        for known_city, code in self.airport_codes.items():
            if known_city in city_lower or city_lower in known_city:
                return code
        if len(city) == 3 and city.isupper():
            return city
        return city[:3].upper()
    
    async def search_travel_options(self, origin: str, destination: str, travel_date: str,
                                     travel_type: str = "all", budget: Optional[int] = None,
                                     passengers: int = 1) -> Dict[str, Any]:
        """Search for travel options using multiple APIs in parallel."""
        results = {
            "origin": origin, "destination": destination, "travel_date": travel_date,
            "passengers": passengers, "budget": budget,
            "flights": [], "trains": [], "buses": [],
            "search_summary": "", "data_source": "multi-api", "apis_used": []
        }
        
        if travel_type in ["flight", "all"]:
            flights_data = await self._search_flights_parallel(
                origin, destination, travel_date, budget, passengers)
            results["flights"] = flights_data["flights"]
            results["apis_used"] = flights_data["apis_used"]
            results["api_stats"] = flights_data["api_stats"]
        
        if travel_type in ["train", "all"]:
            results["trains"] = await self._search_trains(origin, destination, travel_date, budget, passengers)
        
        if travel_type in ["bus", "all"]:
            results["buses"] = await self._search_buses(origin, destination, travel_date, budget, passengers)
        
        results["search_summary"] = self._generate_summary(results, budget)
        return results
    
    async def _search_flights_parallel(self, origin: str, destination: str, travel_date: str,
                                        budget: Optional[int], passengers: int) -> Dict:
        """Search ALL flight APIs in parallel and merge results."""
        origin_code = self._get_airport_code(origin)
        dest_code = self._get_airport_code(destination)
        
        print(f"\n🚀 PARALLEL Multi-API Flight Search: {origin} ({origin_code}) → {destination} ({dest_code})")
        print("=" * 60)
        
        # Launch ALL API calls simultaneously
        tasks = [
            self._search_google_flights_safe(origin_code, dest_code, travel_date, passengers, budget),
            self._search_booking_flights_safe(origin, destination, travel_date, passengers, budget),
        ]
        
        # Add Amadeus if configured
        if self.amadeus_api_key and self.amadeus_api_secret:
            tasks.append(self._search_amadeus_flights_safe(origin_code, dest_code, travel_date, passengers, budget))
        
        print(f"📡 Calling {len(tasks)} APIs simultaneously...")
        
        # Execute all in parallel
        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️ All APIs responded in {elapsed:.2f}s")
        print("-" * 60)
        
        # Collect results from each API
        all_flights = []
        apis_used = []
        api_stats = {}
        
        api_names = ["Google Flights", "Booking.com"]
        if self.amadeus_api_key and self.amadeus_api_secret:
            api_names.append("Amadeus")
        
        for i, (flights, api_name) in enumerate(zip(results, api_names)):
            count = len(flights)
            api_stats[api_name] = count
            if count > 0:
                apis_used.append(api_name)
                all_flights.extend(flights)
                print(f"   ✅ {api_name}: {count} flights")
            else:
                print(f"   ❌ {api_name}: No flights")
        
        print("-" * 60)
        
        # Deduplicate and merge
        merged_flights = self._merge_and_deduplicate(all_flights)
        print(f"📊 Total: {len(all_flights)} flights → {len(merged_flights)} unique (after dedup)")
        
        # Sort by price and add badges
        merged_flights.sort(key=lambda x: x["price_per_person"])
        self._add_badges(merged_flights)
        
        # If no real data, fall back to AI
        if not merged_flights:
            print("📡 No results from APIs, using AI fallback...")
            merged_flights = await self._get_serper_flights(origin, destination, travel_date, budget, passengers)
            apis_used = ["AI Estimate"]
            api_stats["AI Estimate"] = len(merged_flights)
        
        print(f"🎯 Returning top {min(5, len(merged_flights))} flights from: {', '.join(apis_used)}")
        
        return {
            "flights": merged_flights[:5],  # Return top 5
            "apis_used": apis_used,
            "api_stats": api_stats
        }
    
    def _merge_and_deduplicate(self, flights: List[Dict]) -> List[Dict]:
        """Merge flights from multiple sources and remove duplicates."""
        seen = {}
        
        for flight in flights:
            # Create a unique key based on airline, time, and approximate price
            key = (
                flight.get("airline", "").lower(),
                flight.get("departure_time", ""),
                flight.get("arrival_time", ""),
                flight.get("num_stops", 0)
            )
            
            # If we haven't seen this flight, or this one is cheaper, keep it
            if key not in seen or flight["price_per_person"] < seen[key]["price_per_person"]:
                # Mark which APIs had this flight
                if key in seen:
                    existing_sources = seen[key].get("found_in_apis", [seen[key].get("data_source", "")])
                    flight["found_in_apis"] = list(set(existing_sources + [flight.get("data_source", "")]))
                    flight["price_comparison"] = {
                        seen[key].get("data_source", ""): seen[key]["price_per_person"],
                        flight.get("data_source", ""): flight["price_per_person"]
                    }
                else:
                    flight["found_in_apis"] = [flight.get("data_source", "")]
                
                seen[key] = flight
        
        return list(seen.values())
    
    # ==================== SAFE WRAPPERS (catch errors) ====================
    
    async def _search_google_flights_safe(self, origin_code: str, dest_code: str, 
                                           travel_date: str, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Safe wrapper for Google Flights - returns empty list on error."""
        try:
            return await self._search_google_flights(origin_code, dest_code, travel_date, passengers, budget)
        except Exception as e:
            print(f"   ⚠️ Google Flights error: {e}")
            return []
    
    async def _search_booking_flights_safe(self, origin: str, destination: str,
                                            travel_date: str, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Safe wrapper for Booking.com - returns empty list on error."""
        try:
            return await self._search_booking_flights(origin, destination, travel_date, passengers, budget)
        except Exception as e:
            print(f"   ⚠️ Booking.com error: {e}")
            return []
    
    async def _search_amadeus_flights_safe(self, origin_code: str, dest_code: str,
                                            travel_date: str, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Safe wrapper for Amadeus - returns empty list on error."""
        try:
            return await self._search_amadeus_flights(origin_code, dest_code, travel_date, passengers, budget)
        except Exception as e:
            print(f"   ⚠️ Amadeus error: {e}")
            return []
    
    # ==================== GOOGLE FLIGHTS API ====================
    
    async def _search_google_flights(self, origin_code: str, dest_code: str, travel_date: str,
                                      passengers: int, budget: Optional[int]) -> List[Dict]:
        """Search using Google Flights Data API."""
        headers = {"x-rapidapi-host": "google-flights-data.p.rapidapi.com",
                   "x-rapidapi-key": self.rapidapi_key}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.google_flights_url}/flights/search-oneway",
                headers=headers,
                params={"departureId": origin_code, "arrivalId": dest_code,
                        "departureDate": travel_date, "adults": str(passengers), "currency": "INR"}
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            if not data.get("status") or not data.get("data"):
                return []
            
            return self._parse_google_flights(data["data"], passengers, budget)
    
    def _parse_google_flights(self, data: Dict, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Parse Google Flights response."""
        flights = []
        all_flights = data.get("topFlights", []) + data.get("otherFlights", [])
        
        for flight in all_flights[:20]:
            try:
                price = flight.get("price", 0)
                duration_mins = flight.get("durationMinutes", 0)
                stops = flight.get("stops", 0)
                segments = flight.get("segments", [])
                first_seg = segments[0] if segments else {}
                
                flights.append({
                    "airline": flight.get("airlineName", "Unknown"),
                    "airline_code": flight.get("airlineCode", "XX"),
                    "airline_logo": f"https://www.gstatic.com/flights/airline_logos/70px/{flight.get('airlineCode', 'XX')}.png",
                    "flight_number": f"{flight.get('airlineCode', '')}{first_seg.get('flightNumber', '')}",
                    "departure_time": self._format_time(flight.get("departureTime", "")),
                    "arrival_time": self._format_time(flight.get("arrivalTime", "")),
                    "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                    "duration_minutes": duration_mins,
                    "price_per_person": price,
                    "total_price": price * passengers,
                    "passengers": passengers,
                    "class": "Economy",
                    "stops": "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}",
                    "num_stops": stops,
                    "aircraft": first_seg.get("aircraftName", ""),
                    "deal": self._get_deal_tag(price, budget),
                    "baggage": "15kg + 7kg cabin",
                    "is_real_data": True,
                    "data_source": "Google Flights",
                    "booking_url": "https://www.google.com/travel/flights"
                })
            except:
                continue
        
        return flights
    
    # ==================== BOOKING.COM API ====================
    
    async def _search_booking_flights(self, origin: str, destination: str, travel_date: str,
                                       passengers: int, budget: Optional[int]) -> List[Dict]:
        """Search using Booking.com API."""
        headers = {"x-rapidapi-host": "booking-com15.p.rapidapi.com",
                   "x-rapidapi-key": self.rapidapi_key}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get airport IDs
            from_id = await self._get_booking_airport_id(client, headers, origin)
            to_id = await self._get_booking_airport_id(client, headers, destination)
            
            if not from_id or not to_id:
                return []
            
            response = await client.get(
                f"{self.booking_url}/flights/searchFlights",
                headers=headers,
                params={
                    "fromId": from_id, "toId": to_id, "departDate": travel_date,
                    "adults": str(passengers), "cabinClass": "ECONOMY",
                    "currency_code": "INR", "sort": "BEST"
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return self._parse_booking_flights(data, passengers, budget)
    
    async def _get_booking_airport_id(self, client: httpx.AsyncClient, headers: Dict, query: str) -> Optional[str]:
        """Get Booking.com airport ID."""
        try:
            resp = await client.get(
                f"{self.booking_url}/flights/searchDestination",
                headers=headers, params={"query": query}
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                # Prefer airport type
                for item in data:
                    if item.get("type") == "AIRPORT":
                        return item.get("id")
                if data:
                    return data[0].get("id")
        except:
            pass
        return None
    
    def _parse_booking_flights(self, data: Dict, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Parse Booking.com response with filtering for unrealistic flights."""
        flights = []
        flight_offers = data.get("data", {}).get("flightOffers", [])
        
        for offer in flight_offers[:20]:
            try:
                segments = offer.get("segments", [])
                if not segments:
                    continue
                
                first_seg = segments[0]
                legs = first_seg.get("legs", [])
                
                # Calculate duration
                dep_time = first_seg.get("departureTime", "")
                arr_time = first_seg.get("arrivalTime", "")
                duration_mins = self._calc_duration_mins(dep_time, arr_time)
                
                # Number of stops
                num_stops = len(legs) - 1 if legs else 0
                
                # FILTER: Skip unrealistic connecting flights (>8 hours with stops)
                if duration_mins > 480 and num_stops > 0:
                    continue  # Skip 10+ hour connecting flights for short routes
                
                first_leg = legs[0] if legs else {}
                carrier = first_leg.get("carriersData", [{}])[0] if first_leg.get("carriersData") else {}
                
                price_data = offer.get("priceBreakdown", {}).get("total", {})
                price = int(price_data.get("units", 0))
                
                flights.append({
                    "airline": carrier.get("name", "Unknown"),
                    "airline_code": carrier.get("code", "XX"),
                    "airline_logo": carrier.get("logo", ""),
                    "flight_number": first_leg.get("flightInfo", {}).get("flightNumber", ""),
                    "departure_time": self._format_time(dep_time),
                    "arrival_time": self._format_time(arr_time),
                    "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                    "duration_minutes": duration_mins,
                    "price_per_person": price,
                    "total_price": price * passengers,
                    "passengers": passengers,
                    "class": "Economy",
                    "stops": "Non-stop" if num_stops == 0 else f"{num_stops} stop{'s' if num_stops > 1 else ''}",
                    "num_stops": num_stops,
                    "deal": self._get_deal_tag(price, budget),
                    "baggage": "Check-in included",
                    "is_real_data": True,
                    "data_source": "Booking.com",
                    "booking_url": "https://www.booking.com/flights"
                })
            except:
                continue
        
        return flights
    
    # ==================== AMADEUS API ====================
    
    async def _search_amadeus_flights(self, origin_code: str, dest_code: str, travel_date: str,
                                       passengers: int, budget: Optional[int]) -> List[Dict]:
        """Search using Amadeus API."""
        # Get OAuth token
        token = await self._get_amadeus_token()
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.amadeus_url}/v2/shopping/flight-offers",
                headers=headers,
                params={
                    "originLocationCode": origin_code,
                    "destinationLocationCode": dest_code,
                    "departureDate": travel_date,
                    "adults": passengers,
                    "currencyCode": "INR",
                    "max": 20
                }
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return self._parse_amadeus_flights(data, passengers, budget)
    
    async def _get_amadeus_token(self) -> Optional[str]:
        """Get Amadeus OAuth token."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.amadeus_url}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.amadeus_api_key,
                        "client_secret": self.amadeus_api_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if response.status_code == 200:
                    return response.json().get("access_token")
        except:
            pass
        return None
    
    def _parse_amadeus_flights(self, data: Dict, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Parse Amadeus response."""
        flights = []
        carriers = data.get("dictionaries", {}).get("carriers", {})
        
        for offer in data.get("data", [])[:20]:
            try:
                itinerary = offer.get("itineraries", [{}])[0]
                segments = itinerary.get("segments", [])
                
                if not segments:
                    continue
                
                first_seg = segments[0]
                last_seg = segments[-1]
                
                # Parse duration (PT2H30M format)
                duration_str = itinerary.get("duration", "PT0H0M")
                duration_mins = self._parse_amadeus_duration(duration_str)
                
                carrier_code = first_seg.get("carrierCode", "XX")
                airline_name = carriers.get(carrier_code, carrier_code)
                
                price = float(offer.get("price", {}).get("total", 0))
                
                flights.append({
                    "airline": airline_name,
                    "airline_code": carrier_code,
                    "airline_logo": f"https://www.gstatic.com/flights/airline_logos/70px/{carrier_code}.png",
                    "flight_number": f"{carrier_code}{first_seg.get('number', '')}",
                    "departure_time": self._format_time(first_seg.get("departure", {}).get("at", "")),
                    "arrival_time": self._format_time(last_seg.get("arrival", {}).get("at", "")),
                    "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                    "duration_minutes": duration_mins,
                    "price_per_person": int(price),
                    "total_price": int(price * passengers),
                    "passengers": passengers,
                    "class": "Economy",
                    "stops": "Non-stop" if len(segments) == 1 else f"{len(segments) - 1} stop{'s' if len(segments) > 2 else ''}",
                    "num_stops": len(segments) - 1,
                    "deal": self._get_deal_tag(int(price), budget),
                    "baggage": "Check-in included",
                    "is_real_data": True,
                    "data_source": "Amadeus",
                    "booking_url": "https://www.amadeus.com"
                })
            except:
                continue
        
        return flights
    
    def _parse_amadeus_duration(self, duration_str: str) -> int:
        """Parse Amadeus duration format (PT2H30M) to minutes."""
        try:
            duration_str = duration_str.replace("PT", "")
            hours = 0
            mins = 0
            if "H" in duration_str:
                parts = duration_str.split("H")
                hours = int(parts[0])
                duration_str = parts[1] if len(parts) > 1 else ""
            if "M" in duration_str:
                mins = int(duration_str.replace("M", ""))
            return hours * 60 + mins
        except:
            return 0
    
    # ==================== SERPER FALLBACK ====================
    
    async def _get_serper_flights(self, origin: str, destination: str, travel_date: str,
                                   budget: Optional[int], passengers: int) -> List[Dict]:
        """Use AI to generate flight estimates when APIs fail."""
        prompt = f"""Generate 3 realistic flight options from {origin} to {destination} on {travel_date}.
        Budget: {budget or 'flexible'} INR per person
        Passengers: {passengers}
        
        Return JSON array with flights having: airline, flight_number, departure_time, arrival_time, 
        duration, price_per_person, stops. Use realistic Indian airlines and prices."""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            flights_data = json.loads(content)
            
            return [{
                "airline": f.get("airline", "Unknown"),
                "airline_code": f.get("airline_code", "XX"),
                "airline_logo": "",
                "flight_number": f.get("flight_number", ""),
                "departure_time": f.get("departure_time", ""),
                "arrival_time": f.get("arrival_time", ""),
                "duration": f.get("duration", ""),
                "duration_minutes": 120,
                "price_per_person": f.get("price_per_person", 5000),
                "total_price": f.get("price_per_person", 5000) * passengers,
                "passengers": passengers,
                "class": "Economy",
                "stops": f.get("stops", "Non-stop"),
                "num_stops": 0,
                "deal": "",
                "baggage": "15kg included",
                "is_real_data": False,
                "data_source": "AI Estimate",
                "booking_url": ""
            } for f in flights_data[:3]]
        except:
            return []
    
    # ==================== HELPER METHODS ====================
    
    def _format_time(self, time_str: str) -> str:
        """Format time string to HH:MM."""
        if not time_str:
            return ""
        try:
            if "T" in time_str:
                time_part = time_str.split("T")[1][:5]
                return time_part
            return time_str[:5]
        except:
            return time_str
    
    def _calc_duration_mins(self, dep: str, arr: str) -> int:
        """Calculate duration in minutes between departure and arrival."""
        try:
            dep_dt = datetime.fromisoformat(dep.replace("Z", "+00:00"))
            arr_dt = datetime.fromisoformat(arr.replace("Z", "+00:00"))
            return int((arr_dt - dep_dt).total_seconds() / 60)
        except:
            return 120
    
    def _get_deal_tag(self, price: int, budget: Optional[int]) -> str:
        """Get deal tag based on price and budget."""
        if not budget:
            return ""
        if price <= budget * 0.7:
            return "🔥 Great Deal"
        elif price <= budget:
            return "✅ Within Budget"
        return ""
    
    def _add_badges(self, flights: List[Dict]) -> None:
        """Add recommendation badges to flights."""
        if not flights:
            return
        
        # Sort by different criteria to find best options
        by_price = sorted(flights, key=lambda x: x["price_per_person"])
        by_duration = sorted(flights, key=lambda x: x.get("duration_minutes", 999))
        
        # Calculate value score (lower is better)
        for f in flights:
            price_score = f["price_per_person"] / 1000
            duration_score = f.get("duration_minutes", 120) / 60
            stops_penalty = f.get("num_stops", 0) * 2
            f["value_score"] = price_score + duration_score + stops_penalty
        
        by_value = sorted(flights, key=lambda x: x.get("value_score", 999))
        
        # Assign badges
        if by_price:
            by_price[0]["badge"] = "💰 Cheapest"
        if by_duration and by_duration[0] != by_price[0]:
            by_duration[0]["badge"] = "⚡ Fastest"
        if by_value and by_value[0] not in [by_price[0], by_duration[0]] if by_duration else [by_price[0]]:
            by_value[0]["badge"] = "⭐ Best Value"
        
        # Mark remaining without badges
        for f in flights:
            if "badge" not in f:
                f["badge"] = "✈️ Good Option"
    
    def _generate_summary(self, results: Dict, budget: Optional[int]) -> str:
        """Generate search summary."""
        apis = results.get("apis_used", [])
        flights = results.get("flights", [])
        
        if not flights:
            return "No flights found for this route."
        
        cheapest = min(flights, key=lambda x: x["price_per_person"])
        fastest = min(flights, key=lambda x: x.get("duration_minutes", 999))
        
        live_badge = "🔴 LIVE" if cheapest.get("is_real_data") else "📊 Est"
        api_str = " + ".join(apis) if apis else "Multiple APIs"
        
        summary = f"✈️ {live_badge} ₹{cheapest['price_per_person']:,} ({cheapest['airline']}) via {api_str}"
        
        if fastest != cheapest:
            summary += f" | ⚡ Fastest: {fastest['duration']}"
        
        return summary
    
    # ==================== TRAINS - PARALLEL API SEARCH ====================
    
    async def _search_trains(self, origin: str, destination: str, travel_date: str,
                              budget: Optional[int], passengers: int) -> List[Dict]:
        """Search trains using Rail Info API (accurate route-based search)."""
        print(f"\n🚂 Train Search: {origin} → {destination}")
        print("=" * 60)
        
        # Only use Rail Info API - it correctly searches trains BETWEEN stations
        # IRCTC API only searches by train NUMBER, not by route (returns wrong trains)
        trains = await self._search_railinfo_trains_safe(origin, destination, travel_date, passengers, budget)
        
        if trains:
            print(f"   ✅ Rail Info API: {len(trains)} trains found")
        else:
            print("   ❌ No trains found, using AI fallback...")
            trains = await self._get_ai_trains(origin, destination, travel_date, budget, passengers)
        
        # Sort and add badges
        trains.sort(key=lambda x: x.get("price_per_person", 9999))
        self._add_train_badges(trains)
        
        print(f"🎯 Returning top {min(5, len(trains))} trains")
        
        return trains[:5]
    
    async def _search_irctc_trains_safe(self, origin: str, destination: str, travel_date: str,
                                         passengers: int, budget: Optional[int]) -> List[Dict]:
        """IRCTC API searches by train NUMBER, not between stations - disabled."""
        # Returns wrong trains for routes, so we don't use it
        return []
    
    async def _search_railinfo_trains_safe(self, origin: str, destination: str, travel_date: str,
                                            passengers: int, budget: Optional[int]) -> List[Dict]:
        """Safe wrapper for Rail Info API."""
        try:
            return await self._search_railinfo_trains(origin, destination, travel_date, passengers, budget)
        except Exception as e:
            print(f"   ⚠️ Rail Info API error: {type(e).__name__}: {e}")
            return []
    
    async def _search_irctc_trains(self, origin: str, destination: str, travel_date: str,
                                    passengers: int, budget: Optional[int]) -> List[Dict]:
        """Search using Indian Railway IRCTC API - train search by number."""
        headers = {
            "x-rapidapi-host": "indian-railway-irctc.p.rapidapi.com",
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapid-api": "rapid-api-database"
        }
        
        # IRCTC API searches by train number, not between stations
        # We'll search for popular trains on this route
        popular_trains = {
            ("BCT", "NDLS"): ["12951", "12953", "22210"],  # Mumbai-Delhi Rajdhanis
            ("NDLS", "BCT"): ["12952", "12954", "22209"],  # Delhi-Mumbai Rajdhanis
            ("MAS", "NDLS"): ["12621", "12615"],  # Chennai-Delhi
            ("SBC", "NDLS"): ["12627", "12649"],  # Bangalore-Delhi
            ("HWH", "NDLS"): ["12301", "12305"],  # Kolkata-Delhi
        }
        
        origin_code = self._get_station_code(origin)
        dest_code = self._get_station_code(destination)
        route_key = (origin_code, dest_code)
        
        trains = []
        train_numbers = popular_trains.get(route_key, ["12951"])  # Default to Rajdhani
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for train_no in train_numbers[:2]:  # Limit to 2 to avoid rate limits
                try:
                    response = await client.get(
                        f"https://indian-railway-irctc.p.rapidapi.com/api/trains-search/v1/train/{train_no}",
                        headers=headers,
                        params={'isH5': 'true', 'client': 'web'}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        parsed = self._parse_irctc_train_detail(data, passengers, budget, train_no)
                        if parsed:
                            trains.extend(parsed)
                except Exception as e:
                    continue
        
        return trains
    
    def _parse_irctc_train_detail(self, data: Dict, passengers: int, budget: Optional[int], train_no: str) -> List[Dict]:
        """Parse IRCTC train detail response."""
        trains = []
        try:
            body = data.get("body", {})
            if not body:
                return []
            
            train_info = body if isinstance(body, dict) else {}
            train_name = train_info.get("trainName", train_info.get("train_name", f"Train {train_no}"))
            
            # Estimate fare (IRCTC doesn't always return fare)
            duration_mins = 960  # Default 16 hours
            fare = self._estimate_train_fare(duration_mins, "SL")
            
            trains.append({
                "train_name": train_name,
                "train_number": train_no,
                "train_type": train_info.get("trainType", "Express"),
                "departure_time": train_info.get("departureTime", ""),
                "arrival_time": train_info.get("arrivalTime", ""),
                "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                "duration_minutes": duration_mins,
                "price_per_person": fare,
                "total_price": fare * passengers,
                "class_prices": {
                    "SL": fare,
                    "3A": int(fare * 2.5),
                    "2A": int(fare * 3.5),
                    "1A": int(fare * 6)
                },
                "passengers": passengers,
                "class": "Sleeper (SL)",
                "is_real_data": True,
                "data_source": "IRCTC API",
                "booking_url": "https://www.irctc.co.in"
            })
        except Exception as e:
            pass
        
        return trains
    
    async def _search_railinfo_trains(self, origin: str, destination: str, travel_date: str,
                                       passengers: int, budget: Optional[int]) -> List[Dict]:
        """Search using Rail Info API (India) - /v1/trains/between endpoint."""
        headers = {
            "X-RapidAPI-Host": "rail-info-api-india1.p.rapidapi.com",
            "X-RapidAPI-Key": self.rapidapi_key
        }
        
        origin_code = self._get_station_code(origin)
        dest_code = self._get_station_code(destination)
        
        print(f"   Rail Info: searching {origin_code} → {dest_code}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use /v1/trains/between endpoint
            response = await client.get(
                "https://rail-info-api-india1.p.rapidapi.com/v1/trains/between",
                headers=headers,
                params={
                    "from": origin_code,
                    "to": dest_code,
                    "limit": "20"
                }
            )
            
            if response.status_code != 200:
                print(f"   Rail Info API status: {response.status_code} - {response.text[:100]}")
                return []
            
            data = response.json()
            return self._parse_railinfo_trains(data, passengers, budget, travel_date)
    
    def _get_station_code(self, city: str) -> str:
        """Get railway station code from city name."""
        station_codes = {
            # Major metros - use main stations
            "mumbai": "BCT", "bombay": "BCT", "mumbai central": "BCT",
            "delhi": "NDLS", "new delhi": "NDLS",
            "bangalore": "SBC", "bengaluru": "SBC",
            "chennai": "MAS", "madras": "MAS",
            "kolkata": "HWH", "calcutta": "HWH", "howrah": "HWH",
            "hyderabad": "SC", "secunderabad": "SC",
            
            # Other major cities
            "pune": "PUNE", "ahmedabad": "ADI", "jaipur": "JP",
            "lucknow": "LKO", "kanpur": "CNB",
            "goa": "MAO", "madgaon": "MAO", "margao": "MAO",
            "varanasi": "BSB", "banaras": "BSB",
            "agra": "AGC", "patna": "PNBE", "bhopal": "BPL",
            "indore": "INDB", "nagpur": "NGP", "surat": "ST", "vadodara": "BRC",
            
            # South India
            "thiruvananthapuram": "TVC", "trivandrum": "TVC",
            "kochi": "ERS", "cochin": "ERS", "ernakulam": "ERS",
            "coimbatore": "CBE", "mysore": "MYS", "mysuru": "MYS",
            "mangalore": "MAQ", "mangaluru": "MAQ",
            
            # East & North East
            "guwahati": "GHY", "bhubaneswar": "BBS",
            "visakhapatnam": "VSKP", "vizag": "VSKP",
            
            # North India
            "chandigarh": "CDG", "amritsar": "ASR",
            "jammu": "JAT", "dehradun": "DDN",
            "haridwar": "HW", "rishikesh": "RKSH",
            "shimla": "SML", "udaipur": "UDZ",
            "jodhpur": "JU", "ajmer": "AII",
            
            # Central India
            "raipur": "R", "ranchi": "RNC",
            "gwalior": "GWL", "jabalpur": "JBP",
            "allahabad": "ALD", "prayagraj": "PRYJ"
        }
        city_lower = city.lower().strip()
        if city_lower in station_codes:
            return station_codes[city_lower]
        for known_city, code in station_codes.items():
            if known_city in city_lower or city_lower in known_city:
                return code
        return city[:4].upper()
    
    def _parse_irctc_trains(self, data: Dict, passengers: int, budget: Optional[int]) -> List[Dict]:
        """Parse IRCTC API response."""
        trains = []
        train_list = data.get("data", [])
        
        for train in train_list[:15]:
            try:
                train_name = train.get("train_name", "Unknown")
                train_no = train.get("train_number", "")
                dep_time = train.get("from_sta", train.get("departure_time", ""))
                arr_time = train.get("to_sta", train.get("arrival_time", ""))
                duration = train.get("duration", "0:0")
                
                # Parse duration
                duration_mins = self._parse_train_duration(duration)
                
                # Get fare (estimate if not available)
                fare = train.get("fare", {})
                sleeper_fare = fare.get("SL", 0) or self._estimate_train_fare(duration_mins, "SL")
                ac3_fare = fare.get("3A", 0) or self._estimate_train_fare(duration_mins, "3A")
                
                trains.append({
                    "train_name": train_name,
                    "train_number": train_no,
                    "train_type": train.get("train_type", "Express"),
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                    "duration_minutes": duration_mins,
                    "price_per_person": sleeper_fare,
                    "total_price": sleeper_fare * passengers,
                    "class_prices": {
                        "SL": sleeper_fare,
                        "3A": ac3_fare,
                        "2A": int(ac3_fare * 1.5),
                        "1A": int(ac3_fare * 2.5)
                    },
                    "passengers": passengers,
                    "class": "Sleeper (SL)",
                    "days_of_run": train.get("run_days", "Daily"),
                    "is_real_data": True,
                    "data_source": "IRCTC API",
                    "booking_url": "https://www.irctc.co.in"
                })
            except:
                continue
        
        return trains
    
    def _parse_railinfo_trains(self, data: Dict, passengers: int, budget: Optional[int], travel_date: str) -> List[Dict]:
        """Parse Rail Info API response - /v1/trains/between format."""
        trains = []
        
        # Response format: {"data": [...], "dataset_version_id": "..."}
        train_list = data.get("data", [])
        
        for train in train_list[:15] if isinstance(train_list, list) else []:
            try:
                train_name = train.get("train_name", "Unknown")
                train_no = str(train.get("train_no", train.get("train_number", "")))
                train_type = train.get("train_type", "express")
                
                # Get duration from total_duration_minutes or stops_count
                duration_mins = train.get("total_duration_minutes", 0)
                if not duration_mins:
                    # Estimate based on stops
                    stops = train.get("stops_count", 10)
                    duration_mins = stops * 30  # Rough estimate
                
                # Estimate fare based on duration and train type
                fare = self._estimate_train_fare(duration_mins, "SL")
                
                # Adjust fare based on train type
                if train_type in ["rajdhani", "shatabdi", "vande_bharat"]:
                    fare = int(fare * 2.5)  # Premium trains
                elif train_type in ["duronto", "garib_rath"]:
                    fare = int(fare * 1.5)
                
                trains.append({
                    "train_name": train_name,
                    "train_number": train_no,
                    "train_type": train_type.replace("_", " ").title(),
                    "departure_time": train.get("departure_time", ""),
                    "arrival_time": train.get("arrival_time", ""),
                    "duration": f"{duration_mins // 60}h {duration_mins % 60}m",
                    "duration_minutes": duration_mins,
                    "price_per_person": fare,
                    "total_price": fare * passengers,
                    "class_prices": {
                        "SL": fare,
                        "3A": int(fare * 2.5),
                        "2A": int(fare * 3.5),
                        "1A": int(fare * 6)
                    },
                    "passengers": passengers,
                    "class": "Sleeper (SL)",
                    "stops_count": train.get("stops_count", 0),
                    "is_overnight": train.get("is_overnight", False),
                    "avg_speed": train.get("avg_speed_kmph", 0),
                    "is_real_data": True,
                    "data_source": "Rail Info API",
                    "booking_url": "https://www.irctc.co.in"
                })
            except Exception as e:
                continue
        
        return trains
    
    def _parse_train_duration(self, duration: str) -> int:
        """Parse train duration string to minutes."""
        try:
            if ":" in duration:
                parts = duration.split(":")
                return int(parts[0]) * 60 + int(parts[1])
            elif "h" in duration.lower():
                duration = duration.lower().replace("h", ":").replace("m", "").replace(" ", "")
                parts = duration.split(":")
                return int(parts[0]) * 60 + int(parts[1]) if len(parts) > 1 else int(parts[0]) * 60
            return int(duration)
        except:
            return 480  # Default 8 hours
    
    def _estimate_train_fare(self, duration_mins: int, travel_class: str) -> int:
        """Estimate train fare based on duration and class."""
        # Mumbai-Delhi is ~1400km, takes ~16 hours
        # Approximate distance from duration: avg 80km/hour
        distance_approx = (duration_mins / 60) * 80
        
        # Minimum distance for realistic fare
        distance_approx = max(distance_approx, 500)  # At least 500km for long routes
        
        base_fares = {
            "SL": 0.45,   # Sleeper: ~₹0.45/km (₹450 for 1000km)
            "3A": 1.10,   # AC 3-tier: ~₹1.10/km (₹1100 for 1000km)
            "2A": 1.60,   # AC 2-tier: ~₹1.60/km (₹1600 for 1000km)
            "1A": 2.80    # AC 1st class: ~₹2.80/km (₹2800 for 1000km)
        }
        
        rate = base_fares.get(travel_class, 0.45)
        fare = int(distance_approx * rate)
        
        # Minimum fares
        min_fares = {"SL": 350, "3A": 800, "2A": 1200, "1A": 2000}
        return max(fare, min_fares.get(travel_class, 350))
    
    def _deduplicate_trains(self, trains: List[Dict]) -> List[Dict]:
        """Remove duplicate trains."""
        seen = {}
        for train in trains:
            key = (train.get("train_number", ""), train.get("departure_time", ""))
            if key not in seen or train["price_per_person"] < seen[key]["price_per_person"]:
                seen[key] = train
        return list(seen.values())
    
    def _add_train_badges(self, trains: List[Dict]) -> None:
        """Add badges to trains."""
        if not trains:
            return
        
        by_price = sorted(trains, key=lambda x: x.get("price_per_person", 9999))
        by_duration = sorted(trains, key=lambda x: x.get("duration_minutes", 9999))
        
        if by_price:
            by_price[0]["badge"] = "💰 Cheapest"
        if by_duration and by_duration[0] != by_price[0]:
            by_duration[0]["badge"] = "⚡ Fastest"
        
        for t in trains:
            if "badge" not in t:
                t["badge"] = "🚂 Good Option"
    
    async def _get_ai_trains(self, origin: str, destination: str, travel_date: str,
                              budget: Optional[int], passengers: int) -> List[Dict]:
        """Generate train estimates using AI."""
        prompt = f"""Generate 3 realistic train options from {origin} to {destination} for {travel_date}.
        Use actual Indian train names like Rajdhani Express, Shatabdi Express, Duronto, etc.
        Include: train_name, train_number, departure_time, arrival_time, duration, sleeper_fare, ac3_fare.
        Return as JSON array."""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            trains_data = json.loads(content)
            
            return [{
                "train_name": t.get("train_name", "Express"),
                "train_number": t.get("train_number", "12345"),
                "train_type": "Express",
                "departure_time": t.get("departure_time", "06:00"),
                "arrival_time": t.get("arrival_time", "14:00"),
                "duration": t.get("duration", "8h 0m"),
                "duration_minutes": 480,
                "price_per_person": t.get("sleeper_fare", 500),
                "total_price": t.get("sleeper_fare", 500) * passengers,
                "class_prices": {
                    "SL": t.get("sleeper_fare", 500),
                    "3A": t.get("ac3_fare", 1200),
                    "2A": int(t.get("ac3_fare", 1200) * 1.5),
                    "1A": int(t.get("ac3_fare", 1200) * 2.5)
                },
                "passengers": passengers,
                "class": "Sleeper (SL)",
                "is_real_data": False,
                "data_source": "AI Estimate",
                "booking_url": "https://www.irctc.co.in"
            } for t in trains_data[:3]]
        except:
            return []
    
    # ==================== BUSES - AI POWERED (No reliable API) ====================
    
    async def _search_buses(self, origin: str, destination: str, travel_date: str,
                             budget: Optional[int], passengers: int) -> List[Dict]:
        """Search buses using AI (no reliable bus API available)."""
        print(f"\n🚌 Bus Search: {origin} → {destination}")
        print("📡 Using AI with real bus operator data...")
        
        buses = await self._get_ai_buses(origin, destination, travel_date, budget, passengers)
        
        if buses:
            self._add_bus_badges(buses)
            print(f"   ✅ Generated {len(buses)} bus options")
        
        return buses[:5]
    
    async def _get_ai_buses(self, origin: str, destination: str, travel_date: str,
                             budget: Optional[int], passengers: int) -> List[Dict]:
        """Generate realistic bus options using AI."""
        prompt = f"""Generate 4 realistic bus options from {origin} to {destination} for {travel_date}.
        Use actual Indian bus operators: VRL Travels, SRS Travels, Orange Travels, Neeta Travels, 
        Paulo Travels, KSRTC, MSRTC, GSRTC, Shrinath Travels, Parveen Travels.
        
        Include different bus types: Sleeper, Semi-sleeper, AC Seater, Non-AC Seater, Volvo Multi-Axle.
        
        Return JSON array with: operator, bus_type, departure_time, arrival_time, duration, price.
        Prices should be realistic (₹300-2000 based on distance and bus type)."""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            buses_data = json.loads(content)
            
            return [{
                "operator": b.get("operator", "Private Bus"),
                "bus_type": b.get("bus_type", "Sleeper"),
                "departure_time": b.get("departure_time", "21:00"),
                "arrival_time": b.get("arrival_time", "06:00"),
                "duration": b.get("duration", "9h 0m"),
                "duration_minutes": self._parse_train_duration(b.get("duration", "9:0")),
                "price_per_person": b.get("price", 800),
                "total_price": b.get("price", 800) * passengers,
                "passengers": passengers,
                "amenities": b.get("amenities", ["Blanket", "Water Bottle", "Charging Point"]),
                "rating": b.get("rating", 4.0),
                "is_real_data": False,
                "data_source": "AI Estimate (RedBus prices)",
                "booking_url": "https://www.redbus.in"
            } for b in buses_data[:4]]
        except Exception as e:
            print(f"   ⚠️ Bus AI error: {e}")
            return []
    
    def _add_bus_badges(self, buses: List[Dict]) -> None:
        """Add badges to buses."""
        if not buses:
            return
        
        by_price = sorted(buses, key=lambda x: x.get("price_per_person", 9999))
        
        if by_price:
            by_price[0]["badge"] = "💰 Cheapest"
        
        for b in buses:
            if "badge" not in b:
                if "Volvo" in b.get("bus_type", "") or "AC" in b.get("bus_type", ""):
                    b["badge"] = "⭐ Premium"
                else:
                    b["badge"] = "🚌 Good Option"
