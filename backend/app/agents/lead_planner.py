from __future__ import annotations

import asyncio
import json
import re
from datetime import timedelta
from typing import Any, Dict, Optional

from groq import Groq

from app.models import ItineraryRequest, ItineraryResponse
from app.tools.places import PlaceDetailsTool
from app.tools.weather import WeatherForecastTool


class LeadPlannerAgent:
    """Coordinates research tools to assemble a structured itinerary using Groq."""

    def __init__(self, groq_api_key: str, maptiler_api_key: str, weather_api_key: str, serper_api_key: Optional[str] = None):
        self._client = Groq(api_key=groq_api_key)
        self._places_tool = PlaceDetailsTool(api_key=maptiler_api_key, serper_api_key=serper_api_key)
        self._weather_tool = WeatherForecastTool(api_key=weather_api_key)

    async def plan_itinerary(self, request: ItineraryRequest) -> ItineraryResponse:
        # First, gather tool data for the destination
        place_data = None
        weather_data = None
        restaurants_data = []
        
        try:
            place_data = await self._places_tool._arun(location=request.destination)
        except Exception as e:
            print(f"Warning: Could not fetch place data: {e}")
        
        try:
            weather_data = await self._weather_tool._arun(location=request.destination)
        except Exception as e:
            print(f"Warning: Could not fetch weather data: {e}")
        
        try:
            restaurants_data = await self._places_tool.fetch_restaurants(request.destination, num=8)
            print(f"Fetched {len(restaurants_data)} real restaurants for {request.destination}")
        except Exception as e:
            print(f"Warning: Could not fetch restaurant data: {e}")

        # Build context from tool results
        tool_context = self._build_tool_context(place_data, weather_data)
        
        # Generate itinerary with Groq (Llama 3)
        prompt = self._build_prompt(request, tool_context)
        
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Lead Planner, an expert AI travel concierge. You create detailed, realistic travel itineraries with specific times for each activity. Always respond with valid JSON only, no markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=8192,
        )
        
        # Parse response
        raw_text = response.choices[0].message.content
        json_str = self._extract_json(raw_text)
        data = json.loads(json_str)
        
        # Inject tool data into response
        data = self._inject_tool_data(data, place_data, weather_data, restaurants_data)
        
        # Fetch real data for each place/attraction in the schedule
        data = await self._enrich_places_with_real_data(data, request.destination)
        
        return ItineraryResponse.model_validate(data)

    def _build_tool_context(self, place_data, weather_data) -> str:
        context_parts = []
        
        if place_data:
            context_parts.append(f"""
DESTINATION INFO:
- Location: {place_data.location}
- Summary: {place_data.summary}
- Photos available: {len(place_data.photos)} images
- Reviews: Rating {place_data.reviews.rating}/5, Highlights: {'; '.join(place_data.reviews.highlights[:3])}
""")
        
        if weather_data:
            forecasts = weather_data.forecast[:7]
            weather_str = "\n".join(
                f"  - {f.date}: {f.summary}, {f.temp_min_c:.0f}°C - {f.temp_max_c:.0f}°C"
                for f in forecasts
            )
            context_parts.append(f"""
WEATHER FORECAST:
{weather_str}
""")
        
        return "\n".join(context_parts) if context_parts else "No external data available."

    def _build_prompt(self, request: ItineraryRequest, tool_context: str) -> str:
        duration = (request.endDate - request.startDate).days + 1
        
        # Generate date strings for each day
        dates = []
        for i in range(duration):
            day_date = request.startDate + timedelta(days=i)
            dates.append(str(day_date))
        
        return f"""Create a DETAILED and REALISTIC day-by-day travel itinerary with SPECIFIC TIMES for each activity.

TRIP DETAILS:
- From: {request.source}
- To: {request.destination}
- Dates: {request.startDate} to {request.endDate} ({duration} days)
- Travelers: {request.people} people
- Budget: ₹{request.budget} INR per person
- Transport: {request.transport}

{tool_context}

⚠️ CRITICAL - REALISTIC TIMING REQUIREMENTS:
1. USE REALISTIC DURATIONS based on actual visit times:
   - Famous temples (like Tirupati, Vaishno Devi): 8-16 hours including queue time
   - Major tourist attractions: 2-4 hours minimum
   - Museums: 2-3 hours
   - Beaches: 2-4 hours
   - Trekking/hiking: actual trek duration + buffer
   - Shopping areas: 2-3 hours
   
2. ACCOUNT FOR PRACTICAL REALITIES:
   - Queue/waiting times at popular places
   - Travel time between locations
   - Rest breaks and meal times
   - Ticket counter closing times
   - Best time to visit (morning/evening) for each place
   
3. INCLUDE PRACTICAL TIPS for each place:
   - When ticket counters open/close
   - Expected waiting time
   - What to carry
   - Dress code requirements
   - Photography restrictions
   - Best visiting hours to avoid crowds

IMPORTANT INSTRUCTIONS:
1. For Day 1: Include departure from {request.source} - reaching airport/station, boarding, travel time, arrival at {request.destination}
2. For each place, provide REALISTIC duration based on actual visitor experiences
3. Include specific times (e.g., "06:00 AM", "10:30 AM", "02:00 PM")
4. For the last day: Include checkout, last activities, and return journey details
5. Include dining recommendations with restaurant names
6. Don't overcrowd the schedule - quality over quantity
7. Factor in realistic travel time between attractions

Generate JSON with this EXACT structure:
{{
  "title": "Trip title",
  "leadPlanner": "Lead Planner AI",
  "summary": "2-3 sentence trip overview",
  "details": {{
    "origin": "{request.source}",
    "destination": "{request.destination}",
    "travelers": {request.people},
    "startDate": "{request.startDate}",
    "endDate": "{request.endDate}",
    "budgetPerPerson": {request.budget},
    "transportPreference": "{request.transport}"
  }},
  "days": [
    {{
      "day": 1,
      "date": "{dates[0] if dates else request.startDate}",
      "title": "Departure & Arrival",
      "summary": "Brief day overview",
      "schedule": [
        {{
          "time": "05:30 AM",
          "activity": "Leave for Airport",
          "description": "Depart from home to reach airport",
          "duration": "1 hour",
          "tips": "Book cab in advance"
        }},
        {{
          "time": "12:30 PM",
          "activity": "Lunch",
          "description": "Enjoy authentic local cuisine",
          "duration": "1 hour",
          "isMeal": true,
          "mealType": "lunch",
          "restaurant": {{
            "name": "Famous Restaurant Name",
            "cuisine": "Local/Indian/Chinese etc",
            "description": "Known for their signature dishes",
            "mustTry": ["Dish 1", "Dish 2"]
          }},
          "tips": "Try their specialty dish. Reservations recommended for weekends."
        }},
        {{
          "time": "02:00 PM",
          "activity": "Visit Place Name",
          "description": "Explore this attraction",
          "duration": "3-4 hours (realistic estimate)",
          "place": {{
            "name": "Attraction Name",
            "description": "What this place offers",
            "rating": 4.3,
            "totalReviews": 1500,
            "reviewSummary": "Visitors love the scenic views.",
            "images": [],
            "address": "Address here",
            "estimatedTime": "3-4 hours including queue",
            "openingHours": "6:00 AM - 9:00 PM"
          }},
          "tips": "Arrive early to avoid queues."
        }},
        {{
          "time": "08:00 PM",
          "activity": "Dinner",
          "description": "Fine dining experience",
          "duration": "1.5 hours",
          "isMeal": true,
          "mealType": "dinner",
          "restaurant": {{
            "name": "Popular Restaurant Name",
            "cuisine": "Seafood/Multi-cuisine etc",
            "description": "Award-winning restaurant",
            "mustTry": ["Signature Dish"]
          }},
          "tips": "Book in advance. Great ambiance for dinner."
        }}
      ],
      "estimatedCost": "₹2000-3000 per person"
    }}
  ],
  "travelTips": ["Tip 1", "Tip 2", "Tip 3"],
  "packingSuggestions": ["Item 1", "Item 2", "Item 3"]
}}

IMPORTANT FOR MEALS:
- Include breakfast, lunch, tea/snack breaks, and dinner as schedule items with "isMeal": true
- For each meal, suggest a SPECIFIC famous restaurant/eatery in {request.destination}
- Include the restaurant name, cuisine type, and must-try dishes

Create detailed schedules for all {duration} days with 5-8 activities per day.
Return ONLY valid JSON, no markdown."""

    def _extract_json(self, text: str) -> str:
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Fix common invalid escape sequences that LLMs produce
        # Replace invalid \X escapes (where X is not a valid escape char) with \\X
        # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        def fix_escapes(s: str) -> str:
            result = []
            i = 0
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    next_char = s[i + 1]
                    # Valid escape sequences
                    if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                        result.append(s[i:i+2])
                        i += 2
                    elif next_char == 'u' and i + 5 < len(s):
                        # Unicode escape \uXXXX
                        result.append(s[i:i+6])
                        i += 6
                    else:
                        # Invalid escape - double the backslash
                        result.append('\\\\')
                        i += 1
                else:
                    result.append(s[i])
                    i += 1
            return ''.join(result)
        
        return fix_escapes(text)

    def _inject_tool_data(self, data: dict, place_data, weather_data, restaurants_data=None) -> dict:
        """Inject real tool data into the response where possible."""
        if not data.get("days"):
            return data
        
        # Distribute restaurants across days
        restaurants_per_day = []
        if restaurants_data:
            num_days = len(data["days"])
            restaurants_list = [r.model_dump(by_alias=True) for r in restaurants_data]
            # Give each day 2-3 restaurants
            for i in range(num_days):
                start_idx = (i * 2) % len(restaurants_list) if restaurants_list else 0
                day_restaurants = []
                if restaurants_list:
                    day_restaurants = [
                        restaurants_list[start_idx % len(restaurants_list)],
                        restaurants_list[(start_idx + 1) % len(restaurants_list)] if len(restaurants_list) > 1 else restaurants_list[0]
                    ]
                    # Add a third restaurant for variety if available
                    if len(restaurants_list) > 2:
                        day_restaurants.append(restaurants_list[(start_idx + 2) % len(restaurants_list)])
                restaurants_per_day.append(day_restaurants)
            
        for idx, day in enumerate(data["days"]):
            # Inject location insight with real data
            if place_data:
                if "locationInsight" not in day or day.get("locationInsight") is None:
                    day["locationInsight"] = {
                        "location": place_data.location,
                        "description": place_data.summary,
                        "photos": [str(p) for p in place_data.photos[:4]],
                        "reviews": {
                            "rating": place_data.reviews.rating,
                            "totalReviews": place_data.reviews.total_reviews,
                            "highlights": place_data.reviews.highlights,
                        },
                        "popularTimes": [
                            {"day": pt.day, "busynessText": pt.busyness_text}
                            for pt in place_data.popular_times[:3]
                        ],
                        "weather": []
                    }
            
            # Inject weather data
            if weather_data and weather_data.forecast:
                day_index = day.get("day", 1) - 1
                if "locationInsight" in day and day["locationInsight"]:
                    if day_index < len(weather_data.forecast):
                        forecast = weather_data.forecast[day_index]
                        day["locationInsight"]["weather"] = [{
                            "date": str(forecast.date),
                            "summary": forecast.summary,
                            "icon": forecast.icon,
                            "tempMinC": forecast.temp_min_c,
                            "tempMaxC": forecast.temp_max_c,
                        }]
            
            # Inject real restaurant recommendations
            if restaurants_per_day and idx < len(restaurants_per_day):
                day["diningRecommendations"] = {
                    "restaurants": restaurants_per_day[idx]
                }
        
        return data

    async def _enrich_places_with_real_data(self, data: dict, destination: str) -> dict:
        """Fetch real Google data for each place/attraction in the schedule."""
        if not data.get("days"):
            return data
        
        # Collect all unique place names from schedule
        places_to_fetch = []
        place_locations = []  # Track (day_idx, schedule_idx) for each place
        
        for day_idx, day in enumerate(data["days"]):
            schedule = day.get("schedule", [])
            for sched_idx, item in enumerate(schedule):
                place = item.get("place")
                if place and place.get("name"):
                    place_name = place["name"]
                    # Skip generic activities like "Airport", "Hotel Check-in"
                    skip_keywords = ["airport", "check-in", "checkout", "check out", "departure", "arrival", "hotel", "taxi", "cab", "transfer"]
                    if not any(kw in place_name.lower() for kw in skip_keywords):
                        places_to_fetch.append(place_name)
                        place_locations.append((day_idx, sched_idx))
        
        if not places_to_fetch:
            print("No places to enrich with real data")
            return data
        
        print(f"Fetching real Google data for {len(places_to_fetch)} places: {places_to_fetch}")
        
        # Fetch real data for each place (limit to avoid rate limits)
        max_places = min(len(places_to_fetch), 10)  # Limit to 10 places per request
        
        for i in range(max_places):
            place_name = places_to_fetch[i]
            day_idx, sched_idx = place_locations[i]
            
            try:
                real_data = await self._places_tool.fetch_attraction_details(place_name, destination)
                
                if real_data:
                    # Update the place with real data
                    existing_place = data["days"][day_idx]["schedule"][sched_idx].get("place", {})
                    
                    # Merge real data with existing (real data takes priority)
                    if real_data.get("rating"):
                        existing_place["rating"] = real_data["rating"]
                    if real_data.get("totalReviews"):
                        existing_place["totalReviews"] = real_data["totalReviews"]
                    if real_data.get("reviewSummary"):
                        existing_place["reviewSummary"] = real_data["reviewSummary"]
                    if real_data.get("address"):
                        existing_place["address"] = real_data["address"]
                    if real_data.get("images") and len(real_data["images"]) > 0:
                        existing_place["images"] = real_data["images"]
                    if real_data.get("name"):
                        existing_place["name"] = real_data["name"]  # Use official name
                    if real_data.get("openingHours"):
                        existing_place["openingHours"] = real_data["openingHours"]
                    
                    data["days"][day_idx]["schedule"][sched_idx]["place"] = existing_place
                    print(f"✓ Enriched '{place_name}' with real data: rating={real_data.get('rating')}, reviews={real_data.get('totalReviews')}")
                
                # Fetch practical info (duration, tips, ticket info, etc.)
                practical_info = await self._places_tool.fetch_practical_info(place_name, destination)
                if practical_info:
                    existing_place = data["days"][day_idx]["schedule"][sched_idx].get("place", {})
                    existing_place["practicalInfo"] = practical_info
                    
                    # Update estimated time with real duration
                    if practical_info.get("typicalDuration"):
                        existing_place["estimatedTime"] = practical_info["typicalDuration"][:100]
                    
                    # Update opening hours
                    if practical_info.get("openingHours") and not existing_place.get("openingHours"):
                        existing_place["openingHours"] = practical_info["openingHours"]
                    
                    # Add practical tips to the schedule item
                    tips_parts = []
                    if practical_info.get("ticketInfo"):
                        tips_parts.append(f"Tickets: {practical_info['ticketInfo'][:80]}")
                    if practical_info.get("importantTips"):
                        tips_parts.append(practical_info["importantTips"][0][:80])
                    if practical_info.get("warnings"):
                        tips_parts.append(f"⚠️ {practical_info['warnings'][0][:60]}")
                    
                    if tips_parts:
                        current_tips = data["days"][day_idx]["schedule"][sched_idx].get("tips", "")
                        new_tips = " | ".join(tips_parts)
                        if current_tips:
                            data["days"][day_idx]["schedule"][sched_idx]["tips"] = f"{current_tips} | {new_tips}"
                        else:
                            data["days"][day_idx]["schedule"][sched_idx]["tips"] = new_tips
                    
                    data["days"][day_idx]["schedule"][sched_idx]["place"] = existing_place
                    print(f"✓ Added practical info for '{place_name}': duration={practical_info.get('typicalDuration', 'N/A')[:50]}")
                    
                if not real_data and not practical_info:
                    print(f"✗ No real data found for '{place_name}'")
                    
            except Exception as e:
                print(f"✗ Error fetching real data for '{place_name}': {e}")
                continue
        
        # Enrich meal items with real restaurant data
        data = await self._enrich_meals_with_restaurant_data(data, destination)
        
        return data

    async def _enrich_meals_with_restaurant_data(self, data: dict, destination: str) -> dict:
        """Fetch real restaurant data for meal schedule items."""
        if not data.get("days"):
            return data
        
        meals_to_fetch = []
        meal_locations = []
        
        # Collect all meal items that have restaurant names
        for day_idx, day in enumerate(data["days"]):
            schedule = day.get("schedule", [])
            for sched_idx, item in enumerate(schedule):
                # Check if this is a meal item
                is_meal = item.get("isMeal") or item.get("is_meal")
                activity_lower = item.get("activity", "").lower()
                
                # Also detect meals by activity name
                if not is_meal:
                    meal_keywords = ["breakfast", "lunch", "dinner", "brunch", "snack", "tea break", "coffee"]
                    is_meal = any(kw in activity_lower for kw in meal_keywords)
                
                if is_meal:
                    restaurant = item.get("restaurant", {})
                    restaurant_name = restaurant.get("name") if isinstance(restaurant, dict) else None
                    
                    if restaurant_name:
                        meals_to_fetch.append(restaurant_name)
                        meal_locations.append((day_idx, sched_idx))
        
        if not meals_to_fetch:
            print("No meal restaurants to enrich")
            return data
        
        print(f"Fetching real data for {len(meals_to_fetch)} restaurants: {meals_to_fetch}")
        
        # Fetch real data for each restaurant (limit to avoid rate limits)
        max_meals = min(len(meals_to_fetch), 8)
        
        for i in range(max_meals):
            restaurant_name = meals_to_fetch[i]
            day_idx, sched_idx = meal_locations[i]
            
            try:
                real_data = await self._places_tool.fetch_restaurant_details(restaurant_name, destination)
                
                if real_data:
                    existing_restaurant = data["days"][day_idx]["schedule"][sched_idx].get("restaurant", {})
                    
                    # Merge real data with existing
                    existing_restaurant["name"] = real_data.get("name", restaurant_name)
                    if real_data.get("cuisine"):
                        existing_restaurant["cuisine"] = real_data["cuisine"]
                    if real_data.get("rating"):
                        existing_restaurant["rating"] = real_data["rating"]
                    if real_data.get("totalReviews"):
                        existing_restaurant["totalReviews"] = real_data["totalReviews"]
                    if real_data.get("priceLevel"):
                        existing_restaurant["priceLevel"] = real_data["priceLevel"]
                    if real_data.get("address"):
                        existing_restaurant["address"] = real_data["address"]
                    if real_data.get("phone"):
                        existing_restaurant["phone"] = real_data["phone"]
                    if real_data.get("website"):
                        existing_restaurant["website"] = real_data["website"]
                    if real_data.get("reviewSnippet"):
                        existing_restaurant["reviewSnippet"] = real_data["reviewSnippet"]
                    if real_data.get("images"):
                        existing_restaurant["images"] = real_data["images"]
                    if real_data.get("openingHours"):
                        existing_restaurant["openingHours"] = real_data["openingHours"]
                    
                    data["days"][day_idx]["schedule"][sched_idx]["restaurant"] = existing_restaurant
                    print(f"✓ Enriched restaurant '{restaurant_name}': rating={real_data.get('rating')}, images={len(real_data.get('images', []))}")
                else:
                    print(f"✗ No real data found for restaurant '{restaurant_name}'")
                    
            except Exception as e:
                print(f"✗ Error fetching restaurant data for '{restaurant_name}': {e}")
                continue
        
        return data

    async def warm_up(self) -> None:
        """Optional hook to pre-load models/tools."""
        await asyncio.sleep(0)
