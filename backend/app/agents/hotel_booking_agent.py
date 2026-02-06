"""
Hotel Booking Agent - Multi-API Hotel Search System
Uses BOTH Booking.com AND Hotels.com APIs for comprehensive real-time hotel data
Parallel API calls for faster results and better price comparison
"""
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from groq import AsyncGroq
from datetime import datetime


class HotelBookingAgent:
    """Agent that finds the best hotels using multiple APIs (Booking.com + Hotels.com)."""
    
    def __init__(self, groq_api_key: str, serper_api_key: str, rapidapi_key: str):
        self.groq_client = AsyncGroq(api_key=groq_api_key)
        self.serper_api_key = serper_api_key
        self.rapidapi_key = rapidapi_key
        self.model = "llama-3.3-70b-versatile"
        
        # Booking.com API config (booking-com15)
        self.booking_base_url = "https://booking-com15.p.rapidapi.com/api/v1"
        self.booking_headers = {
            "x-rapidapi-host": "booking-com15.p.rapidapi.com",
            "x-rapidapi-key": self.rapidapi_key
        }
        
        # Booking.com API v2 config (Things4u - booking-com18)
        self.booking2_base_url = "https://booking-com18.p.rapidapi.com"
        self.booking2_headers = {
            "x-rapidapi-host": "booking-com18.p.rapidapi.com",
            "x-rapidapi-key": self.rapidapi_key
        }
        
        # Keep backward compatibility
        self.headers = self.booking_headers
    
    async def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        rooms: int = 1,
        budget_per_night: Optional[int] = None,
        hotel_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Search for hotels and return best 3 options with REAL DATA and IMAGES!
        Uses Booking.com API for real-time hotel data.
        """
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (check_out_date - check_in_date).days
        
        results = {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "guests": guests,
            "rooms": rooms,
            "budget_per_night": budget_per_night,
            "hotels": [],
            "search_summary": "",
            "data_source": "real-time",
            "api_sources": []
        }
        
        # Search BOTH APIs in parallel for better coverage and price comparison
        print(f"🏨 Searching hotels from multiple APIs...")
        hotels = await self._search_hotels_multi_api(destination, check_in, check_out, guests, rooms, budget_per_night, hotel_type, nights)
        
        # Track which APIs provided data
        api_sources = set()
        for hotel in hotels:
            if hotel.get("data_source"):
                api_sources.add(hotel["data_source"])
        results["api_sources"] = list(api_sources)
        
        # Add AI review analysis for top hotels
        hotels_with_analysis = await self._add_review_analysis(hotels, destination)
        
        # Rank and select best 3
        results["hotels"] = self._rank_hotels(hotels_with_analysis, budget_per_night, nights, rooms)[:3]
        
        # Generate summary
        results["search_summary"] = self._generate_summary(results)
        
        return results
    
    async def _search_hotels_multi_api(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int,
        budget: Optional[int],
        hotel_type: str,
        nights: int
    ) -> List[Dict[str, Any]]:
        """Search hotels from multiple Booking.com APIs in parallel."""
        
        # Run both API searches concurrently
        results = await asyncio.gather(
            self._search_booking_com(destination, check_in, check_out, guests, rooms, budget, hotel_type, nights),
            self._search_booking_com_v2(destination, check_in, check_out, guests, rooms, budget, nights),
            return_exceptions=True
        )
        
        all_hotels = []
        seen_hotels = set()  # Track by name to avoid duplicates
        
        api_names = ["Booking.com (v1)", "Booking.com (Things4u)"]
        for i, result in enumerate(results):
            api_name = api_names[i]
            if isinstance(result, Exception):
                print(f"❌ {api_name} error: {result}")
            elif isinstance(result, list):
                print(f"✅ {api_name}: Found {len(result)} hotels")
                for hotel in result:
                    # Deduplicate by hotel name (normalized)
                    hotel_key = hotel.get("name", "").lower().replace(" ", "").replace("-", "")[:30]
                    if hotel_key and hotel_key not in seen_hotels:
                        seen_hotels.add(hotel_key)
                        all_hotels.append(hotel)
                    elif hotel_key in seen_hotels:
                        # If duplicate, keep the one with better price
                        for existing in all_hotels:
                            if existing.get("name", "").lower().replace(" ", "").replace("-", "")[:30] == hotel_key:
                                if hotel.get("price_total", 999999) < existing.get("price_total", 999999):
                                    all_hotels.remove(existing)
                                    all_hotels.append(hotel)
                                break
        
        print(f"📊 Total unique hotels: {len(all_hotels)}")
        
        if not all_hotels:
            print("⚠️ No hotels from APIs, using fallback...")
            return await self._get_fallback_hotels(destination, budget, guests)
        
        return all_hotels
    
    async def _search_booking_com_v2(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int,
        budget: Optional[int],
        nights: int
    ) -> List[Dict[str, Any]]:
        """Search hotels using Booking.com API v2 (Things4u - booking-com18)."""
        hotels = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Get destination ID using auto-complete
                autocomplete_response = await client.get(
                    f"{self.booking2_base_url}/stays/auto-complete",
                    headers=self.booking2_headers,
                    params={"query": destination, "languageCode": "en-us"}
                )
                
                if autocomplete_response.status_code != 200:
                    print(f"Booking.com v2 autocomplete error: {autocomplete_response.status_code}")
                    return []
                
                autocomplete_data = autocomplete_response.json()
                
                # Parse destination ID (it's a base64 encoded JSON)
                location_id = None
                suggestions = autocomplete_data.get("data", [])
                
                for item in suggestions:
                    # Get the id which is a base64 encoded location identifier
                    location_id = item.get("id")
                    if location_id:
                        break
                
                if not location_id:
                    print(f"Booking.com v2: Could not find destination for {destination}")
                    return []
                
                print(f"🏨 Booking.com v2: Searching in {destination}")
                
                # Step 2: Search hotels with CORRECT parameter names
                search_params = {
                    "locationId": location_id,  # Correct: locationId not dest_id
                    "checkinDate": check_in,    # Correct: checkinDate not checkin
                    "checkoutDate": check_out,  # Correct: checkoutDate not checkout
                    "adults": guests,
                    "rooms": rooms,
                    "currency": "INR",
                    "languageCode": "en-us"
                }
                
                search_response = await client.get(
                    f"{self.booking2_base_url}/stays/search",
                    headers=self.booking2_headers,
                    params=search_params
                )
                
                if search_response.status_code != 200:
                    print(f"Booking.com v2 search error: {search_response.status_code}")
                    return []
                
                search_data = search_response.json()
                
                if not search_data.get("status"):
                    print(f"Booking.com v2: Search failed - {search_data.get('message')}")
                    return []
                
                # Parse hotel results - data is a list of hotels
                results_list = search_data.get("data", [])
                
                for hotel_data in results_list[:15]:  # Limit to 15 hotels
                    try:
                        hotel_id = hotel_data.get("id", "")
                        name = hotel_data.get("name", "Unknown Hotel")
                        
                        # Get price from priceBreakdown.grossPrice
                        price_breakdown = hotel_data.get("priceBreakdown", {})
                        gross_price = price_breakdown.get("grossPrice", {})
                        total_price = int(gross_price.get("value", 0))
                        
                        # Get excluded price (before additional taxes)
                        excluded = price_breakdown.get("excludedPrice", {})
                        excluded_price = int(excluded.get("value", 0)) if excluded else 0
                        
                        # Get strikethrough (original price)
                        strikethrough = price_breakdown.get("strikethroughPrice", {})
                        original_price = int(strikethrough.get("value", 0)) if strikethrough else None
                        
                        if not total_price:
                            continue
                        
                        # Get images from mainPhotoId
                        images = []
                        main_photo = hotel_data.get("mainPhotoId", "")
                        if main_photo:
                            images.append(f"https://cf.bstatic.com/xdata/images/hotel/max1024x768/{main_photo}.jpg")
                            images.append(f"https://cf.bstatic.com/xdata/images/hotel/square600/{main_photo}.jpg")
                        
                        # Get photo URLs if available
                        photo_urls = hotel_data.get("photoUrls", [])
                        for url in photo_urls[:3]:
                            images.append(url)
                        
                        # Get rating
                        review_score = hotel_data.get("reviewScore", 0)
                        review_count = hotel_data.get("reviewCount", 0)
                        review_word = hotel_data.get("reviewScoreWord", self._get_review_word(review_score))
                        
                        # Get star rating - use propertyClass or accuratePropertyClass
                        star_rating = hotel_data.get("propertyClass", 0) or hotel_data.get("accuratePropertyClass", 3)
                        
                        # Get location
                        latitude = hotel_data.get("latitude", 0)
                        longitude = hotel_data.get("longitude", 0)
                        country_code = hotel_data.get("countryCode", "in")
                        
                        # Get check-in/out times
                        checkin_info = hotel_data.get("checkin", {})
                        checkout_info = hotel_data.get("checkout", {})
                        
                        # Calculate per night
                        price_per_night = int(total_price / nights) if nights > 0 else total_price
                        
                        # Apply budget filter
                        if budget and price_per_night > budget * 1.5:
                            continue
                        
                        # Get deal/discount info
                        deal = ""
                        benefit_badges = price_breakdown.get("benefitBadges", [])
                        for badge in benefit_badges:
                            badge_text = badge.get("text", "")
                            if badge_text:
                                deal = f"🏷️ {badge_text}"
                                break
                        
                        if original_price and original_price > total_price:
                            discount = int((original_price - total_price) / original_price * 100)
                            deal = f"🔥 {discount}% off! Save ₹{int(original_price - total_price)}"
                        
                        if not deal:
                            deal = "Best available rate"
                        
                        hotel = {
                            "id": f"booking2_{hotel_id}",
                            "name": name,
                            "star_rating": int(star_rating) if star_rating else 3,
                            "location": destination,
                            "latitude": latitude,
                            "longitude": longitude,
                            "price_total": total_price,
                            "price_with_taxes": total_price,
                            "price_per_night": price_per_night,
                            "original_price": original_price,
                            "currency": "INR",
                            "images": images,
                            "main_image": images[0] if images else "https://via.placeholder.com/600x400?text=Hotel",
                            "google_rating": review_score,
                            "review_score": review_score,
                            "review_word": review_word,
                            "total_reviews": review_count,
                            "check_in_time": checkin_info.get("fromTime", "14:00"),
                            "check_out_time": checkout_info.get("untilTime", "11:00"),
                            "deal": deal,
                            "booking_url": f"https://www.booking.com/hotel/{country_code}/{name.lower().replace(' ', '-').replace(',', '')}.html",
                            "is_real_data": True,
                            "is_preferred": hotel_data.get("isPreferredPlus", False),
                            "amenities": [],
                            "room_type": "Standard Room",
                            "data_source": "Booking.com (Things4u)"
                        }
                        
                        hotels.append(hotel)
                        
                    except Exception as e:
                        print(f"Error parsing Booking.com v2 hotel: {e}")
                        continue
                
                return hotels
                
        except Exception as e:
            print(f"Booking.com v2 search error: {e}")
            return []
    
    def _get_review_word(self, score: float) -> str:
        """Convert numeric score to review word."""
        if score >= 9:
            return "Exceptional"
        elif score >= 8:
            return "Excellent"
        elif score >= 7:
            return "Very Good"
        elif score >= 6:
            return "Good"
        elif score >= 5:
            return "Fair"
        else:
            return "Average"
    
    async def _search_booking_com(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int,
        budget: Optional[int],
        hotel_type: str,
        nights: int
    ) -> List[Dict[str, Any]]:
        """Search hotels using Booking.com API."""
        try:
            # Get destination ID
            dest_info = await self._get_destination_id(destination)
            
            if not dest_info:
                print(f"Booking.com: Could not find destination: {destination}")
                return []
            
            print(f"🏨 Booking.com: Searching in {dest_info['name']} (ID: {dest_info['dest_id']})")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {
                    "dest_id": dest_info["dest_id"],
                    "search_type": dest_info["search_type"],
                    "arrival_date": check_in,
                    "departure_date": check_out,
                    "adults": guests,
                    "room_qty": rooms,
                    "currency_code": "INR",
                    "page_number": 1
                }
                
                # Add price filter if budget specified
                if budget:
                    params["price_max"] = budget
                
                response = await client.get(
                    f"{self.booking_base_url}/hotels/searchHotels",
                    headers=self.booking_headers,
                    params=params
                )
                
                if response.status_code != 200:
                    print(f"Booking.com API error: {response.status_code}")
                    return []
                
                data = response.json()
                
                if not data.get("status") or not data.get("data"):
                    return []
                
                # Parse hotel results (use existing parser but add data_source)
                hotels = self._parse_hotel_results(data["data"], destination, budget, nights)
                
                # Add data source
                for hotel in hotels:
                    hotel["data_source"] = "Booking.com"
                
                return hotels
                
        except Exception as e:
            print(f"Booking.com search error: {e}")
            return []
    
    async def _get_destination_id(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get destination ID from Booking.com API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.booking_base_url}/hotels/searchDestination",
                    headers=self.headers,
                    params={"query": destination}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") and data.get("data"):
                        # Return first city result
                        for item in data["data"]:
                            if item.get("search_type") in ["city", "district", "region"]:
                                return {
                                    "dest_id": item.get("dest_id"),
                                    "search_type": item.get("search_type"),
                                    "name": item.get("name"),
                                    "image_url": item.get("image_url")
                                }
                        # Fallback to first result
                        if data["data"]:
                            return {
                                "dest_id": data["data"][0].get("dest_id"),
                                "search_type": data["data"][0].get("search_type"),
                                "name": data["data"][0].get("name")
                            }
                return None
        except Exception as e:
            print(f"Error getting destination ID for {destination}: {e}")
            return None
    
    async def _search_hotels_real(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int,
        budget: Optional[int],
        hotel_type: str
    ) -> List[Dict[str, Any]]:
        """Search for REAL hotels using Booking.com API with images."""
        try:
            # Get destination ID
            dest_info = await self._get_destination_id(destination)
            
            if not dest_info:
                print(f"Could not find destination: {destination}")
                return await self._get_fallback_hotels(destination, budget, guests)
            
            print(f"🏨 Searching hotels in {dest_info['name']} (ID: {dest_info['dest_id']})")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {
                    "dest_id": dest_info["dest_id"],
                    "search_type": dest_info["search_type"],
                    "arrival_date": check_in,
                    "departure_date": check_out,
                    "adults": guests,
                    "room_qty": rooms,
                    "currency_code": "INR",
                    "page_number": 1
                }
                
                # Add price filter if budget specified
                if budget:
                    params["price_max"] = budget
                
                response = await client.get(
                    f"{self.booking_base_url}/hotels/searchHotels",
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code != 200:
                    print(f"Hotel API error: {response.status_code}")
                    return await self._get_fallback_hotels(destination, budget, guests)
                
                data = response.json()
                
                if not data.get("status") or not data.get("data"):
                    return await self._get_fallback_hotels(destination, budget, guests)
                
                # Parse hotel results
                hotels = self._parse_hotel_results(data["data"], destination, budget)
                
                return hotels if hotels else await self._get_fallback_hotels(destination, budget, guests)
                
        except Exception as e:
            print(f"Real hotel search error: {e}")
            return await self._get_fallback_hotels(destination, budget, guests)
    
    def _parse_hotel_results(
        self,
        data: Dict,
        destination: str,
        budget: Optional[int],
        nights: int = 1
    ) -> List[Dict[str, Any]]:
        """Parse Booking.com hotel API response with images."""
        hotels = []
        
        try:
            hotel_list = data.get("hotels", [])
            
            for hotel_data in hotel_list[:15]:  # Process top 15
                try:
                    property_info = hotel_data.get("property", {})
                    
                    # Extract basic info
                    name = property_info.get("name", "Unknown Hotel")
                    hotel_id = property_info.get("id", hotel_data.get("hotel_id"))
                    
                    # Get images - Booking.com provides multiple sizes
                    photo_urls = property_info.get("photoUrls", [])
                    # Use the larger images (square1024 or square2000)
                    images = []
                    for url in photo_urls[:5]:  # Get up to 5 images
                        # Convert to max resolution
                        if "square500" in url:
                            images.append(url.replace("square500", "square600"))
                        elif "square1024" in url:
                            images.append(url.replace("square1024", "max1024x768"))
                        else:
                            images.append(url)
                    
                    # If no photoUrls, try to construct from mainPhotoId
                    if not images and property_info.get("mainPhotoId"):
                        photo_id = property_info["mainPhotoId"]
                        images = [
                            f"https://cf.bstatic.com/xdata/images/hotel/max1024x768/{photo_id}.jpg",
                            f"https://cf.bstatic.com/xdata/images/hotel/square600/{photo_id}.jpg"
                        ]
                    
                    # Get pricing
                    price_breakdown = property_info.get("priceBreakdown", {})
                    
                    # Booking.com API provides:
                    # - grossPrice: Total with all taxes (what you pay)
                    # - excludedPrice: Price before additional taxes (what Booking.com shows)
                    # We show excludedPrice to match Booking.com website display
                    
                    gross_price = price_breakdown.get("grossPrice", {})
                    excluded_price = price_breakdown.get("excludedPrice", {})
                    
                    # Use excluded price (matches website) or fall back to gross
                    if excluded_price and excluded_price.get("value"):
                        display_price = float(excluded_price.get("value", 0))
                        total_price = int(display_price)
                        # Store gross for reference
                        total_with_taxes = int(gross_price.get("value", display_price))
                    else:
                        display_price = float(gross_price.get("value", 0))
                        total_price = int(display_price)
                        total_with_taxes = total_price
                    
                    currency = gross_price.get("currency", "INR")
                    
                    # Calculate per night price immediately
                    price_per_night = int(total_price / nights) if nights > 0 else total_price
                    
                    # Check for discount
                    strikethrough = price_breakdown.get("strikethroughPrice", {})
                    original_price = int(strikethrough.get("value", 0)) if strikethrough else None
                    
                    # Get rating info
                    review_score = property_info.get("reviewScore", 0)
                    review_count = property_info.get("reviewCount", 0)
                    review_word = property_info.get("reviewScoreWord", "Good")
                    
                    # Get star rating
                    star_rating = property_info.get("propertyClass", property_info.get("accuratePropertyClass", 3))
                    
                    # Get location info
                    latitude = property_info.get("latitude", 0)
                    longitude = property_info.get("longitude", 0)
                    country_code = property_info.get("countryCode", "")
                    
                    # Get check-in/out times
                    checkin_info = property_info.get("checkin", {})
                    checkout_info = property_info.get("checkout", {})
                    
                    # Build deal text
                    deal = ""
                    if original_price and original_price > total_price:
                        discount = int((original_price - total_price) / original_price * 100)
                        deal = f"🔥 {discount}% off! Save ₹{int(original_price - total_price)}"
                    
                    # Check for benefit badges
                    benefit_badges = price_breakdown.get("benefitBadges", [])
                    for badge in benefit_badges:
                        if badge.get("text"):
                            deal = f"🏷️ {badge['text']}" if not deal else f"{deal} | {badge['text']}"
                    
                    if not deal:
                        deal = "Best available rate"
                    
                    hotel = {
                        "id": hotel_id,
                        "name": name,
                        "star_rating": star_rating,
                        "location": destination,
                        "latitude": latitude,
                        "longitude": longitude,
                        "price_total": total_price,  # Display price (excludes some taxes)
                        "price_with_taxes": total_with_taxes,  # Full price with all taxes
                        "price_per_night": price_per_night,  # Calculated per night
                        "original_price": original_price,
                        "currency": currency,
                        "images": images,
                        "main_image": images[0] if images else "https://via.placeholder.com/600x400?text=Hotel",
                        "google_rating": review_score,
                        "review_score": review_score,
                        "review_word": review_word,
                        "total_reviews": review_count,
                        "check_in_time": checkin_info.get("fromTime", "14:00"),
                        "check_out_time": checkout_info.get("untilTime", "11:00"),
                        "deal": deal,
                        "booking_url": f"https://www.booking.com/hotel/{country_code.lower()}/{name.lower().replace(' ', '-')}.html",
                        "is_real_data": True,
                        "is_preferred": property_info.get("isPreferred", False),
                        "amenities": [],  # Will be populated from details if needed
                        "room_type": "Standard Room",
                        "data_source": "Booking.com"
                    }
                    
                    hotels.append(hotel)
                    
                except Exception as e:
                    print(f"Error parsing hotel: {e}")
                    continue
            
            # Sort by review score
            hotels.sort(key=lambda x: (x.get("review_score", 0), -x.get("price_total", 0)), reverse=True)
            
            return hotels
            
        except Exception as e:
            print(f"Error in _parse_hotel_results: {e}")
            return []
    
    async def _add_review_analysis(
        self,
        hotels: List[Dict[str, Any]],
        destination: str
    ) -> List[Dict[str, Any]]:
        """Add AI-powered review analysis to hotels."""
        
        for hotel in hotels[:5]:  # Analyze top 5 hotels
            try:
                # Generate review analysis using LLM based on available data
                analysis = await self._generate_review_analysis(hotel)
                hotel["review_analysis"] = analysis
                
            except Exception as e:
                print(f"Review analysis error for {hotel.get('name')}: {e}")
                hotel["review_analysis"] = self._get_default_analysis(hotel)
        
        # Add default analysis for remaining hotels
        for hotel in hotels[5:]:
            hotel["review_analysis"] = self._get_default_analysis(hotel)
        
        return hotels
    
    async def _generate_review_analysis(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI review analysis for a hotel."""
        
        prompt = f"""Analyze this hotel and generate a review summary:

Hotel: {hotel.get('name')}
Rating: {hotel.get('review_score', 'N/A')}/10 ({hotel.get('review_word', 'Good')})
Reviews: {hotel.get('total_reviews', 0)} reviews
Stars: {hotel.get('star_rating', 3)} star
Location: {hotel.get('location')}
Price: ₹{hotel.get('price_total', 0)}

Based on typical guest experiences at {hotel.get('star_rating', 3)}-star hotels with {hotel.get('review_score', 7)}/10 rating, generate:

{{
  "summary": "2-sentence summary of likely guest experience",
  "pros": ["3 likely positive points"],
  "cons": ["2 potential concerns"],
  "sentiment_score": {min(5, hotel.get('review_score', 7) / 2)},
  "cleanliness_score": 4.0,
  "service_score": 4.0,
  "value_score": 3.8,
  "best_for": ["Ideal guest types"],
  "standout_feature": "Main highlight"
}}

Return ONLY the JSON object."""

        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Review generation error: {e}")
            return self._get_default_analysis(hotel)
    
    def _get_default_analysis(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Get default review analysis based on hotel data."""
        score = hotel.get("review_score", 7)
        stars = hotel.get("star_rating", 3)
        
        return {
            "summary": f"A well-rated {stars}-star hotel with good reviews from guests. Offers comfortable accommodation and good service.",
            "pros": ["Good location", "Clean rooms", "Helpful staff"],
            "cons": ["Standard amenities"],
            "sentiment_score": min(5, score / 2),
            "cleanliness_score": min(5, (score / 2) + 0.3),
            "service_score": min(5, score / 2),
            "value_score": min(5, (score / 2) - 0.2),
            "best_for": ["Tourists", "Business travelers"],
            "standout_feature": "Central location with good reviews"
        }
    
    def _rank_hotels(
        self,
        hotels: List[Dict[str, Any]],
        budget: Optional[int],
        nights: int,
        rooms: int
    ) -> List[Dict[str, Any]]:
        """Rank hotels based on multiple factors."""
        
        for hotel in hotels:
            review_analysis = hotel.get("review_analysis", {})
            
            # Calculate composite score
            rating_score = (hotel.get("review_score", 7) / 10) * 10  # Max 10
            sentiment_score = review_analysis.get("sentiment_score", 3.5) * 2  # Max 10
            value_score = review_analysis.get("value_score", 3.5) * 2  # Max 10
            
            # Price factor
            price = hotel.get("price_total", 5000)
            if budget:
                price_score = max(0, 10 - (price / budget * 5)) if price <= budget * nights else 0
            else:
                price_score = 5
            
            # Preferred property bonus
            preferred_bonus = 1 if hotel.get("is_preferred") else 0
            
            # Composite score
            composite_score = (
                rating_score * 0.30 +
                sentiment_score * 0.25 +
                value_score * 0.20 +
                price_score * 0.20 +
                preferred_bonus * 0.05
            )
            
            hotel["composite_score"] = round(composite_score, 2)
            hotel["nights"] = nights
            hotel["rooms"] = rooms
            
            # Recalculate per night price
            hotel["price_per_night"] = int(price / nights) if nights > 0 else price
            
            # Also calculate price with taxes per night for transparency
            price_with_taxes = hotel.get("price_with_taxes", price)
            hotel["price_per_night_with_taxes"] = int(price_with_taxes / nights) if nights > 0 else price_with_taxes
            
            # Generate recommendation
            hotel["why_recommended"] = self._get_recommendation_reason(hotel, review_analysis)
            
            # Check value
            hotel["is_good_value"] = value_score >= 7 and (not budget or price <= budget * nights)
        
        # Sort by composite score
        hotels.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
        
        # Add badges
        if len(hotels) >= 1:
            hotels[0]["badge"] = "🏆 Best Overall"
        if len(hotels) >= 2:
            hotels[1]["badge"] = "⭐ Highly Rated"
        if len(hotels) >= 3:
            # Find best value among top hotels
            best_value_idx = min(range(min(5, len(hotels))), key=lambda i: hotels[i].get("price_total", 999999))
            if best_value_idx >= 2:
                hotels[2]["badge"] = "💰 Best Value"
            else:
                hotels[2]["badge"] = "👍 Great Choice"
        
        return hotels
    
    def _get_recommendation_reason(self, hotel: Dict[str, Any], review_analysis: Dict[str, Any]) -> str:
        """Generate recommendation reason."""
        reasons = []
        
        score = hotel.get("review_score", 0)
        if score >= 9:
            reasons.append("Exceptional reviews")
        elif score >= 8:
            reasons.append("Highly rated")
        elif score >= 7:
            reasons.append("Well rated")
        
        if hotel.get("is_preferred"):
            reasons.append("Booking.com Preferred")
        
        standout = review_analysis.get("standout_feature", "")
        if standout:
            reasons.append(standout.lower())
        
        value = review_analysis.get("value_score", 0)
        if value >= 4:
            reasons.append("great value")
        
        if not reasons:
            reasons.append("Good choice for your stay")
        
        return reasons[0].capitalize() + (f" with {reasons[1]}" if len(reasons) > 1 else "")
    
    async def _get_fallback_hotels(
        self,
        destination: str,
        budget: Optional[int],
        guests: int
    ) -> List[Dict[str, Any]]:
        """Generate LLM-based hotel data when API fails."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.serper_api_key},
                    json={"q": f"best hotels in {destination} reviews booking", "num": 10}
                )
                search_data = response.json()
                
                # Also get images
                img_response = await client.post(
                    "https://google.serper.dev/images",
                    headers={"X-API-KEY": self.serper_api_key},
                    json={"q": f"hotels in {destination}", "num": 10}
                )
                images = img_response.json().get("images", []) if img_response.status_code == 200 else []
            
            image_urls = [img.get("imageUrl", "") for img in images[:10]]
            
            prompt = f"""Generate 5 realistic hotels in {destination}.
Budget: {f'₹{budget}/night' if budget else 'No limit'}

Search context: {json.dumps(search_data.get('organic', [])[:5])}

Return JSON array with real hotel-like names:
[{{
  "name": "Hotel Name",
  "star_rating": 4,
  "location": "{destination}",
  "price_total": 5000,
  "price_per_night": 5000,
  "images": ["{image_urls[0] if image_urls else ''}"],
  "main_image": "{image_urls[0] if image_urls else 'https://via.placeholder.com/600x400?text=Hotel'}",
  "review_score": 8.5,
  "review_word": "Very Good",
  "total_reviews": 1200,
  "deal": "Special offer",
  "booking_url": "https://www.booking.com/",
  "is_real_data": false,
  "amenities": ["WiFi", "Breakfast", "Pool"],
  "room_type": "Deluxe Room"
}}]

Return ONLY the JSON array."""

            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            hotels = json.loads(content)
            
            # Add images from search
            for i, hotel in enumerate(hotels):
                if i < len(image_urls) and image_urls[i]:
                    hotel["images"] = [image_urls[i]]
                    hotel["main_image"] = image_urls[i]
            
            return hotels
            
        except Exception as e:
            print(f"Fallback hotel error: {e}")
            return self._get_simulated_hotels(destination, budget)
    
    def _get_simulated_hotels(self, destination: str, budget: Optional[int]) -> List[Dict[str, Any]]:
        """Static fallback hotel data."""
        return [
            {
                "name": f"Taj {destination}",
                "star_rating": 5,
                "location": destination,
                "price_total": 8500,
                "price_per_night": 8500,
                "images": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600"],
                "main_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600",
                "review_score": 9.2,
                "review_word": "Superb",
                "total_reviews": 3250,
                "deal": "Breakfast included",
                "booking_url": "https://www.booking.com/",
                "is_real_data": False,
                "amenities": ["WiFi", "Breakfast", "Pool", "Spa", "Gym"],
                "room_type": "Deluxe Room",
                "badge": "🏆 Best Overall"
            },
            {
                "name": f"Radisson Blu {destination}",
                "star_rating": 4,
                "location": destination,
                "price_total": 5200,
                "price_per_night": 5200,
                "images": ["https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600"],
                "main_image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600",
                "review_score": 8.5,
                "review_word": "Very Good",
                "total_reviews": 2180,
                "deal": "Free cancellation",
                "booking_url": "https://www.booking.com/",
                "is_real_data": False,
                "amenities": ["WiFi", "Breakfast", "Pool", "Gym"],
                "room_type": "Superior Room",
                "badge": "⭐ Highly Rated"
            },
            {
                "name": f"Lemon Tree Premier {destination}",
                "star_rating": 4,
                "location": destination,
                "price_total": 3800,
                "price_per_night": 3800,
                "images": ["https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600"],
                "main_image": "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600",
                "review_score": 8.0,
                "review_word": "Very Good",
                "total_reviews": 1890,
                "deal": "Best price guarantee",
                "booking_url": "https://www.booking.com/",
                "is_real_data": False,
                "amenities": ["WiFi", "Breakfast", "Restaurant"],
                "room_type": "Executive Room",
                "badge": "💰 Best Value"
            }
        ]
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate search summary."""
        hotels = results.get("hotels", [])
        budget = results.get("budget_per_night")
        nights = results.get("nights", 1)
        
        if not hotels:
            return "No hotels found matching your criteria"
        
        summary_parts = []
        
        # Check for real data
        real_data = any(h.get("is_real_data") for h in hotels)
        if real_data:
            summary_parts.append("🔴 LIVE prices from Booking.com")
        
        # Best rated
        best_rated = max(hotels, key=lambda x: x.get("review_score", 0))
        summary_parts.append(f"⭐ Top rated: {best_rated['name']} ({best_rated.get('review_score', 'N/A')}/10)")
        
        # Price range
        prices = [h.get("price_per_night", 0) for h in hotels if h.get("price_per_night")]
        if prices:
            summary_parts.append(f"💵 ₹{min(prices):,} - ₹{max(prices):,}/night")
        
        # Budget match
        if budget:
            within_budget = [h for h in hotels if h.get("price_per_night", 999999) <= budget]
            summary_parts.append(f"📊 {len(within_budget)}/{len(hotels)} within budget")
        
        return " | ".join(summary_parts)
    
    async def get_hotel_details(self, hotel_id: str, destination: str) -> Dict[str, Any]:
        """Get detailed information about a specific hotel."""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.booking_base_url}/hotels/getHotelDetails",
                    headers=self.headers,
                    params={
                        "hotel_id": hotel_id,
                        "currency_code": "INR"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") and data.get("data"):
                        return self._parse_hotel_details(data["data"])
            
            return {"error": "Could not fetch hotel details"}
            
        except Exception as e:
            print(f"Hotel details error: {e}")
            return {"error": str(e)}
    
    def _parse_hotel_details(self, data: Dict) -> Dict[str, Any]:
        """Parse detailed hotel information."""
        try:
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "address": data.get("address", ""),
                "facilities": data.get("facilities", []),
                "images": data.get("photos", []),
                "review_summary": data.get("review_summary", {}),
                "policies": data.get("policies", {}),
                "rooms": data.get("rooms", [])
            }
        except:
            return {"error": "Failed to parse hotel details"}
