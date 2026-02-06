"""
Place Research Agent - Specialized agent for researching places and attractions
Fetches real information about visit duration, opening hours, special events, practical tips
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import httpx

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_PLACES_URL = "https://google.serper.dev/places"


class PlaceResearchAgent:
    """Agent specialized in researching detailed information about places and attractions."""
    
    name = "Place Research Agent"
    description = "Researches real information about places - visit duration, opening hours, special events, tips"
    
    def __init__(self, serper_api_key: str, rapidapi_key: str = None):
        self.serper_api_key = serper_api_key
        self.rapidapi_key = rapidapi_key
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
    
    async def research_place(self, place_name: str, location: str, visit_date: str = None) -> Dict[str, Any]:
        """
        Research comprehensive information about a place.
        """
        print(f"🔍 [Place Research Agent] Researching '{place_name}' in {location}...")
        
        result = {
            "name": place_name,
            "location": location,
            "visit_duration": None,
            "opening_hours": None,
            "ticket_info": None,
            "special_events": [],
            "practical_tips": [],
            "warnings": [],
            "best_time_to_visit": None,
            "dress_code": None,
            "facilities": [],
        }
        
        try:
            # 1. Get basic place info
            place_info = await self._fetch_place_details(place_name, location)
            if place_info:
                result["opening_hours"] = place_info.get("openingHours")
                result["address"] = place_info.get("address")
                result["phone"] = place_info.get("phoneNumber")
                result["website"] = place_info.get("website")
            
            # 2. Get visit duration
            duration_info = await self._search_visit_duration(place_name, location)
            result["visit_duration"] = duration_info
            
            # 3. Get practical tips and warnings
            tips_info = await self._search_practical_tips(place_name, location)
            result["practical_tips"] = tips_info.get("tips", [])
            result["warnings"] = tips_info.get("warnings", [])
            result["ticket_info"] = tips_info.get("ticket_info")
            result["dress_code"] = tips_info.get("dress_code")
            
            # 4. Get special events (if date provided)
            if visit_date:
                events = await self._search_special_events(place_name, location, visit_date)
                result["special_events"] = events
            
            # 5. Get best time to visit
            best_time = await self._search_best_time(place_name, location)
            result["best_time_to_visit"] = best_time
            
            print(f"✓ [Place Research Agent] Completed research for '{place_name}'")
            
        except Exception as e:
            print(f"✗ [Place Research Agent] Error researching {place_name}: {e}")
        
        return result
    
    async def _fetch_place_details(self, place_name: str, location: str) -> Optional[Dict]:
        """Fetch basic place details from Google Places via Serper."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location}", "num": 1}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                return places[0] if places else None
            except:
                return None
    
    async def _search_visit_duration(self, place_name: str, location: str) -> Optional[str]:
        """Search for typical visit duration."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                queries = [
                    f"{place_name} {location} how much time needed visit duration",
                    f"{place_name} how long does darshan take waiting time"
                ]
                
                for query in queries:
                    resp = await client.post(
                        SERPER_SEARCH_URL,
                        headers=self.headers,
                        json={"q": query, "num": 5}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Check answer box first
                    if data.get("answerBox"):
                        answer = data["answerBox"].get("snippet") or data["answerBox"].get("answer")
                        if answer:
                            return answer[:200]
                    
                    # Check organic results
                    for result in data.get("organic", [])[:3]:
                        snippet = result.get("snippet", "").lower()
                        if any(word in snippet for word in ["hour", "minute", "time", "duration", "takes"]):
                            return result.get("snippet", "")[:200]
                
                return None
            except:
                return None
    
    async def _search_practical_tips(self, place_name: str, location: str) -> Dict[str, Any]:
        """Search for practical tips, tickets, dress code, warnings."""
        result = {"tips": [], "warnings": [], "ticket_info": None, "dress_code": None}
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location} visitor tips ticket price entry fee dress code", "num": 8}
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("organic", [])[:5]:
                    snippet = item.get("snippet", "")
                    snippet_lower = snippet.lower()
                    
                    # Ticket info
                    if any(word in snippet_lower for word in ["ticket", "entry fee", "₹", "rs", "free entry", "inr"]):
                        if not result["ticket_info"]:
                            result["ticket_info"] = snippet[:150]
                    
                    # Dress code
                    if any(word in snippet_lower for word in ["dress code", "wear", "clothing", "not allowed", "covered"]):
                        if not result["dress_code"]:
                            result["dress_code"] = snippet[:150]
                    
                    # Tips
                    if any(word in snippet_lower for word in ["tip", "recommend", "best", "should", "must"]):
                        result["tips"].append(snippet[:120])
                    
                    # Warnings
                    if any(word in snippet_lower for word in ["warning", "caution", "avoid", "don't", "not allowed", "queue", "crowd"]):
                        result["warnings"].append(snippet[:120])
                
                result["tips"] = result["tips"][:3]
                result["warnings"] = result["warnings"][:2]
                
            except:
                pass
        
        return result
    
    async def _search_special_events(self, place_name: str, location: str, visit_date: str) -> List[str]:
        """Search for special events on the visit date."""
        events = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Parse month from visit_date
                from datetime import datetime
                date_obj = datetime.strptime(visit_date, "%Y-%m-%d")
                month_name = date_obj.strftime("%B")
                
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location} festival event {month_name} {date_obj.year}", "num": 5}
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("organic", [])[:3]:
                    snippet = item.get("snippet", "")
                    if any(word in snippet.lower() for word in ["festival", "event", "celebration", "special", "ceremony"]):
                        events.append(snippet[:150])
                
            except:
                pass
        
        return events[:2]
    
    async def _search_best_time(self, place_name: str, location: str) -> Optional[str]:
        """Search for best time to visit."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location} best time to visit morning evening", "num": 3}
                )
                resp.raise_for_status()
                data = resp.json()
                
                if data.get("answerBox"):
                    return data["answerBox"].get("snippet", "")[:150]
                
                for item in data.get("organic", [])[:2]:
                    snippet = item.get("snippet", "")
                    if any(word in snippet.lower() for word in ["best time", "morning", "evening", "early", "avoid"]):
                        return snippet[:150]
                
            except:
                pass
        
        return None
    
    async def get_crowd_predictions(self, place_name: str, location: str, place_type: str = None) -> Dict[str, Any]:
        """
        Get crowd prediction patterns for a place.
        Returns peak hours, best times, and crowd levels.
        """
        crowdData = {
            "peakHours": {},
            "bestTimes": [],
            "crowdLevel": "moderate",
            "recommendations": []
        }
        
        try:
            # Search for crowd patterns
            async with httpx.AsyncClient(timeout=15) as client:
                query = f"{place_name} {location} busy hours peak time crowd when to visit"
                
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": query, "num": 8}
                )
                resp.raise_for_status()
                data = resp.json()
                
                # Collect information from search results
                all_snippets = []
                
                if data.get("answerBox"):
                    all_snippets.append(data["answerBox"].get("snippet", ""))
                
                for item in data.get("organic", [])[:6]:
                    snippet = item.get("snippet", "")
                    if snippet:
                        all_snippets.append(snippet)
            
            # Use LLM to extract crowd patterns from search results
            from groq import Groq
            llm = Groq(api_key=self.__dict__.get('groq_api_key', ''))
            
            # If no groq_api_key, generate realistic default patterns based on place type
            if not hasattr(self, 'groq_api_key'):
                return self._generate_default_crowd_patterns(place_name, place_type)
            
            combined_text = "\n".join(all_snippets[:5])
            
            prompt = f"""Analyze the following information about {place_name} in {location} and extract crowd patterns.
Return JSON with this exact structure:
{{
  "peakHours": {{
    "morning": {{"start": "HH:MM", "end": "HH:MM", "crowdLevel": "light/moderate/heavy"}},
    "afternoon": {{"start": "HH:MM", "end": "HH:MM", "crowdLevel": "light/moderate/heavy"}},
    "evening": {{"start": "HH:MM", "end": "HH:MM", "crowdLevel": "light/moderate/heavy"}}
  }},
  "bestTimes": ["time 1", "time 2", "time 3"],
  "crowdLevel": "light/moderate/heavy",
  "recommendations": ["tip 1", "tip 2", "tip 3"]
}}

Search results:
{combined_text}

If no crowd information is found, provide reasonable defaults based on the place type."""

            # For now, return default patterns (we'll integrate with orchestrator's LLM)
            return self._generate_default_crowd_patterns(place_name, place_type)
            
        except Exception as e:
            print(f"✗ Error fetching crowd predictions: {e}")
            return self._generate_default_crowd_patterns(place_name, place_type)
    
    def _generate_default_crowd_patterns(self, place_name: str, place_type: str = None) -> Dict[str, Any]:
        """Generate realistic default crowd patterns based on place type."""
        
        # Define patterns for different place types
        patterns = {
            "temple": {
                "peakHours": {
                    "morning": {"start": "06:00", "end": "09:00", "crowdLevel": "moderate"},
                    "afternoon": {"start": "12:00", "end": "14:00", "crowdLevel": "heavy"},
                    "evening": {"start": "17:00", "end": "20:00", "crowdLevel": "heavy"}
                },
                "bestTimes": ["Early morning (6-7 AM)", "Late evening (after 7 PM)", "Weekday mornings"],
                "crowdLevel": "heavy",
                "recommendations": ["Visit early morning for best experience", "Weekends are heavily crowded", "Evening is moderately crowded"]
            },
            "museum": {
                "peakHours": {
                    "morning": {"start": "09:00", "end": "11:00", "crowdLevel": "light"},
                    "afternoon": {"start": "14:00", "end": "16:00", "crowdLevel": "moderate"},
                    "evening": {"start": "16:00", "end": "18:00", "crowdLevel": "heavy"}
                },
                "bestTimes": ["Weekday mornings", "9-11 AM", "Tuesday-Thursday"],
                "crowdLevel": "moderate",
                "recommendations": ["Avoid weekends", "Best visited in morning hours", "Weekday evenings can be busy"]
            },
            "market": {
                "peakHours": {
                    "morning": {"start": "08:00", "end": "11:00", "crowdLevel": "moderate"},
                    "afternoon": {"start": "13:00", "end": "17:00", "crowdLevel": "heavy"},
                    "evening": {"start": "18:00", "end": "21:00", "crowdLevel": "heavy"}
                },
                "bestTimes": ["Early morning (before 9 AM)", "Weekday mornings", "Just after opening"],
                "crowdLevel": "heavy",
                "recommendations": ["Go early before lunch rush", "Avoid weekends and evenings", "Best on weekday mornings"]
            },
            "beach": {
                "peakHours": {
                    "morning": {"start": "06:00", "end": "09:00", "crowdLevel": "light"},
                    "afternoon": {"start": "12:00", "end": "16:00", "crowdLevel": "heavy"},
                    "evening": {"start": "17:00", "end": "20:00", "crowdLevel": "moderate"}
                },
                "bestTimes": ["Early morning", "Sunset time (evening)", "Weekday mornings"],
                "crowdLevel": "moderate",
                "recommendations": ["Morning swimming is safest and least crowded", "Avoid midday sun and crowds", "Sunset is popular but manageable"]
            },
            "restaurant": {
                "peakHours": {
                    "morning": {"start": "08:00", "end": "10:00", "crowdLevel": "light"},
                    "afternoon": {"start": "12:30", "end": "14:00", "crowdLevel": "heavy"},
                    "evening": {"start": "19:00", "end": "21:00", "crowdLevel": "heavy"}
                },
                "bestTimes": ["11:30 AM - 12:00 PM", "2:30 PM - 5:00 PM", "After 9:30 PM"],
                "crowdLevel": "moderate",
                "recommendations": ["Avoid lunch (12:30-2 PM) and dinner rush (7-9 PM)", "Best to go just before rush hours", "Weekday lunches are quieter"]
            },
            "park": {
                "peakHours": {
                    "morning": {"start": "06:00", "end": "09:00", "crowdLevel": "light"},
                    "afternoon": {"start": "14:00", "end": "17:00", "crowdLevel": "moderate"},
                    "evening": {"start": "17:30", "end": "20:00", "crowdLevel": "heavy"}
                },
                "bestTimes": ["Early morning jogging hours", "Weekday afternoons", "After 8 PM (if allowed)"],
                "crowdLevel": "light",
                "recommendations": ["Early morning is peaceful and uncrowded", "Avoid evening rush after offices close", "Weekday visits are less crowded"]
            }
        }
        
        # Determine place type
        determined_type = place_type
        if not determined_type:
            place_lower = place_name.lower()
            if any(word in place_lower for word in ["temple", "church", "mosque", "shrine"]):
                determined_type = "temple"
            elif any(word in place_lower for word in ["museum", "gallery", "art"]):
                determined_type = "museum"
            elif any(word in place_lower for word in ["market", "bazaar", "mall"]):
                determined_type = "market"
            elif any(word in place_lower for word in ["beach", "shore", "coast"]):
                determined_type = "beach"
            elif any(word in place_lower for word in ["restaurant", "cafe", "hotel", "diner", "eatery"]):
                determined_type = "restaurant"
            elif any(word in place_lower for word in ["park", "garden", "green", "forest"]):
                determined_type = "park"
            else:
                determined_type = "temple"  # default
        
        return patterns.get(determined_type, patterns["temple"])
