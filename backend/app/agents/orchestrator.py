"""
Agent Orchestrator - Coordinates all specialized agents for travel planning
This is the main multi-agent system controller
"""
from __future__ import annotations

import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from groq import AsyncGroq

from app.agents.weather_agent import WeatherAgent
from app.agents.place_research_agent import PlaceResearchAgent
from app.agents.photo_review_agent import PhotoReviewAgent
from app.agents.dining_agent import DiningAgent
from app.agents.city_explorer_agent import CityExplorerAgent
from app.agents.replanning_agent import ReplanningAgent


class AgentOrchestrator:
    """
    Multi-Agent Orchestrator for AI Travel Planning.
    
    Coordinates specialized agents:
    1. Lead Planner - Creates the main itinerary structure
    2. Weather Agent - Researches weather and provides recommendations
    3. Place Research Agent - Gathers detailed place information
    4. Photo & Review Agent - Fetches real photos and reviews
    5. Dining Agent - Finds restaurants for meals
    6. City Explorer Agent - Researches city-level highlights
    7. Replanning Agent - Handles user modifications via chat
    """
    
    def __init__(
        self,
        groq_api_key: str,
        serper_api_key: str,
        weather_api_key: str,
        model: str = "llama-3.3-70b-versatile"
    ):
        self.groq_api_key = groq_api_key
        self.serper_api_key = serper_api_key
        self.weather_api_key = weather_api_key
        self.model = model
        
        # Initialize LLM client for main planning
        self.llm_client = AsyncGroq(api_key=groq_api_key)
        
        # Initialize all specialized agents
        self.weather_agent = WeatherAgent(api_key=weather_api_key)
        self.place_research_agent = PlaceResearchAgent(serper_api_key=serper_api_key)
        self.photo_review_agent = PhotoReviewAgent(serper_api_key=serper_api_key)
        self.dining_agent = DiningAgent(serper_api_key=serper_api_key)
        self.city_explorer_agent = CityExplorerAgent(serper_api_key=serper_api_key, groq_api_key=groq_api_key)
        self.replanning_agent = ReplanningAgent(groq_api_key=groq_api_key, model=model)
        
        print("🤖 [Orchestrator] Multi-Agent System Initialized")
        print(f"   ├── Weather Agent")
        print(f"   ├── Place Research Agent")
        print(f"   ├── Photo & Review Agent")
        print(f"   ├── Dining Agent")
        print(f"   ├── City Explorer Agent")
        print(f"   └── Replanning Agent")
    
    async def plan_trip(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: int,
        interests: List[str] = None,
        travel_style: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Main orchestration method - coordinates all agents to create a comprehensive itinerary.
        """
        print(f"\n{'='*60}")
        print(f"🚀 [Orchestrator] Starting Multi-Agent Trip Planning")
        print(f"   Destination: {destination}")
        print(f"   Dates: {start_date} to {end_date}")
        print(f"   Budget: ₹{budget:,}")
        print(f"{'='*60}\n")
        
        result = {
            "success": False,
            "itinerary": None,
            "weather_data": None,
            "city_highlights": None,
            "agent_contributions": {},
            "errors": [],
        }
        
        try:
            # ===== PHASE 1: Parallel Initial Research =====
            print("📊 [Phase 1] Parallel Initial Research...")
            
            # Run weather and city research in parallel
            weather_task = asyncio.create_task(
                self.weather_agent.research(destination, start_date, end_date)
            )
            city_task = asyncio.create_task(
                self.city_explorer_agent.explore_city(destination, [start_date, end_date])
            )
            
            # Wait for both
            weather_data, city_data = await asyncio.gather(weather_task, city_task)
            
            result["weather_data"] = weather_data
            result["city_highlights"] = city_data
            result["agent_contributions"]["weather_agent"] = weather_data.get("success", False)
            result["agent_contributions"]["city_explorer_agent"] = bool(city_data.get("famous_food"))
            
            print(f"   ✓ Weather Agent: {'Success' if weather_data.get('success') else 'Limited data'}")
            print(f"   ✓ City Explorer Agent: Found {len(city_data.get('famous_food', []))} famous foods")
            
            # ===== PHASE 1.5: Generate Planning Intelligence =====
            print("\n🧠 [Phase 1.5] Generating Planning Intelligence...")
            planning_insights = await self._generate_planning_intelligence(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                interests=interests,
                weather_data=weather_data,
                city_data=city_data,
            )
            print(f"   ✓ Planning intelligence generated")
            
            # ===== PHASE 2: Generate Base Itinerary =====
            print("\n📝 [Phase 2] Generating Optimized Itinerary...")
            
            base_itinerary = await self._generate_base_itinerary(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                interests=interests,
                travel_style=travel_style,
                weather_context=weather_data,
                city_context=city_data,
                planning_insights=planning_insights,
            )
            
            if not base_itinerary:
                result["errors"].append("Failed to generate base itinerary")
                return result
            
            print(f"   ✓ Generated {len(base_itinerary.get('days', []))} days itinerary")
            
            # ===== PHASE 3: Parallel Place Enrichment =====
            print("\n🔍 [Phase 3] Enriching Places with Real Data...")
            
            enriched_itinerary = await self._enrich_places_parallel(
                base_itinerary, 
                destination
            )
            
            # ===== PHASE 4: Restaurant Research for Meals =====
            print("\n🍽️ [Phase 4] Finding Restaurants for Meals...")
            
            final_itinerary = await self._enrich_meals_parallel(
                enriched_itinerary,
                destination
            )
            
            # ===== PHASE 5: Final Assembly =====
            print("\n📦 [Phase 5] Final Assembly...")
            
            # Add weather data to itinerary
            final_itinerary["weather"] = {
                "summary": weather_data.get("summary") if isinstance(weather_data, dict) else None,
                "forecasts": weather_data.get("forecast", []) if isinstance(weather_data, dict) else [],
                "recommendations": weather_data.get("recommendations", []) if isinstance(weather_data, dict) else [],
            }
            
            # Add city highlights
            final_itinerary["cityHighlights"] = {
                "famousFood": city_data.get("famous_food", []),
                "famousRestaurants": city_data.get("famous_restaurants", []),
                "localSpecialties": city_data.get("local_specialties", []),
                "shoppingAreas": city_data.get("shopping_areas", []),
                "festivalsEvents": city_data.get("festivals_events", []),
                "localTips": city_data.get("local_tips", []),
                "transportTips": city_data.get("transport_tips", []),
                "hiddenGems": city_data.get("hidden_gems", []),
                "safetyInfo": city_data.get("safety_info"),
            }
            
            result["success"] = True
            result["itinerary"] = final_itinerary
            
            print(f"\n{'='*60}")
            print(f"✅ [Orchestrator] Multi-Agent Planning Complete!")
            print(f"   Total Days: {len(final_itinerary.get('days', []))}")
            print(f"   Places Enriched: {self._count_enriched_places(final_itinerary)}")
            print(f"   Meals with Restaurants: {self._count_meals_with_restaurants(final_itinerary)}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"✗ [Orchestrator] Error: {e}")
            import traceback
            traceback.print_exc()
            result["errors"].append(str(e))
        
        return result
    
    async def _generate_base_itinerary(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: int,
        interests: List[str],
        travel_style: str,
        weather_context: Dict,
        city_context: Dict,
        planning_insights: Dict = None,
    ) -> Optional[Dict[str, Any]]:
        """Generate the base itinerary structure using LLM with planning intelligence."""
        
        # Calculate number of days
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = (end - start).days + 1
        
        # Build context from other agents
        weather_summary = ""
        if weather_context.get("success"):
            weather_summary = f"""
WEATHER INFORMATION (from Weather Agent):
{weather_context.get('summary', 'Weather data available')}
Recommendations: {', '.join(weather_context.get('recommendations', [])[:3])}
"""
        
        city_summary = ""
        if city_context:
            famous_food = [f.get("name", "") for f in city_context.get("famous_food", [])[:3]]
            city_summary = f"""
CITY HIGHLIGHTS (from City Explorer Agent):
- Famous Food: {', '.join(famous_food) if famous_food else 'Various local cuisines'}
- Famous Restaurants: {len(city_context.get('famous_restaurants', []))} iconic places identified
- Local Tips: {len(city_context.get('local_tips', []))} tips available
"""
        
        # Build planning intelligence context
        planning_context = ""
        if planning_insights:
            planning_context = f"""
PLANNING INTELLIGENCE (APPLY THESE TO CREATE AN OPTIMIZED ITINERARY):

🔄 ROUTE OPTIMIZATION:
{planning_insights.get('routeOptimization', 'Group nearby attractions together')}

⏰ CROWD TIMING (VERY IMPORTANT - schedule visits during best windows):
{self._format_crowd_tips(planning_insights.get('crowdTiming', []))}

🌤️ WEATHER-BASED SCHEDULING:
{self._format_weather_routing(planning_insights.get('weatherRouting', []))}

💰 BUDGET GUIDANCE:
{planning_insights.get('budgetGuidance', 'Stay within reasonable budget')}

🎫 TICKETING CONSIDERATIONS:
{planning_insights.get('ticketingNotes', 'Check advance booking requirements')}

🚗 TRANSIT RECOMMENDATIONS:
{planning_insights.get('transitRecommendations', 'Use local transport between locations')}

👔 LOCAL ETIQUETTE:
{self._format_list(planning_insights.get('etiquetteTips', []))}

🌙 SAFETY CONSIDERATIONS:
{self._format_list(planning_insights.get('safetyTips', []))}

🍽️ FOOD TRAIL (include these dishes in meal recommendations):
{self._format_food_trail(planning_insights.get('foodTrail', []))}
"""

        prompt = f"""You are an expert travel planner creating a detailed day-by-day itinerary.

TRIP DETAILS:
- Destination: {destination}
- Start Date: {start_date}
- End Date: {end_date}
- Duration: {num_days} days
- Budget: ₹{budget:,} (Indian Rupees)
- Interests: {', '.join(interests) if interests else 'General sightseeing'}
- Travel Style: {travel_style}

{weather_summary}
{city_summary}
{planning_context}

CRITICAL REQUIREMENTS:

1. REALISTIC TIMING (VERY IMPORTANT):
   - Famous temples (Tirupati, Meenakshi, etc.): 4-8 hours including queue
   - Regular temples: 1-2 hours
   - Museums: 2-3 hours
   - Beaches: 2-3 hours
   - Shopping areas: 2-3 hours
   - Hill stations/viewpoints: 1-2 hours

2. MEAL BREAKS (MANDATORY):
   - Breakfast: Around 8:00-9:00 AM (30-45 mins)
   - Lunch: Around 12:30-2:00 PM (45-60 mins)
   - Tea/Snacks: Around 4:00-5:00 PM (30 mins)
   - Dinner: Around 7:30-9:00 PM (60 mins)
   Mark meals with "isMeal": true and "mealType": "breakfast/lunch/tea/dinner"

3. APPLY PLANNING INTELLIGENCE:
   - Schedule crowded places during best timing windows (from crowd timing above)
   - Avoid outdoor activities during peak heat if weather suggests
   - Group nearby attractions to minimize travel time
   - Include recommended local dishes in meal stops
   - Apply etiquette tips to relevant activities

4. LOGICAL FLOW:
   - Group nearby attractions together
   - Account for travel time between places
   - Don't rush between distant locations
   - End each day by 9-10 PM

4. ALL COSTS IN INDIAN RUPEES (₹)

Generate a JSON itinerary with this structure:
{{
    "destination": "{destination}",
    "startDate": "{start_date}",
    "endDate": "{end_date}",
    "totalBudget": {budget},
    "currency": "INR",
    "days": [
        {{
            "day": 1,
            "date": "{start_date}",
            "theme": "Day theme",
            "schedule": [
                {{
                    "time": "06:00",
                    "activity": "Activity name",
                    "duration": "2 hours",
                    "place": {{
                        "name": "Place name",
                        "type": "temple/museum/beach/etc"
                    }},
                    "tips": "Useful tip",
                    "isMeal": false
                }},
                {{
                    "time": "09:00",
                    "activity": "Breakfast",
                    "duration": "45 minutes",
                    "isMeal": true,
                    "mealType": "breakfast"
                }}
            ]
        }}
    ],
    "packingList": ["item1", "item2"],
    "budgetBreakdown": {{
        "accommodation": 0,
        "food": 0,
        "transport": 0,
        "activities": 0
    }},
    "emergencyContacts": []
}}

Return ONLY valid JSON, no additional text."""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert travel planner. Generate detailed, realistic travel itineraries. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"✗ [Orchestrator] Base itinerary generation failed: {e}")
            return None
    
    def _format_crowd_tips(self, crowd_data: List) -> str:
        """Format crowd timing data for prompt."""
        if not crowd_data:
            return "- Visit popular places early morning (6-8 AM) to avoid crowds"
        tips = []
        for item in crowd_data[:5]:
            if isinstance(item, dict):
                tips.append(f"- {item.get('place', 'Place')}: Best {item.get('bestTime', 'morning')}, Avoid {item.get('avoidTime', 'afternoon')}")
            else:
                tips.append(f"- {item}")
        return "\n".join(tips) if tips else "- Visit popular places early morning to avoid crowds"
    
    def _format_weather_routing(self, weather_data: List) -> str:
        """Format weather routing for prompt."""
        if not weather_data:
            return "- Schedule outdoor activities in morning/evening, indoor during midday heat"
        tips = []
        for item in weather_data[:4]:
            if isinstance(item, dict):
                tips.append(f"- Day {item.get('day', '')}: {item.get('suggestion', '')}")
            else:
                tips.append(f"- {item}")
        return "\n".join(tips) if tips else "- Schedule outdoor activities wisely based on weather"
    
    def _format_list(self, items: List) -> str:
        """Format a list for prompt."""
        if not items:
            return "- Follow local customs and dress modestly at religious sites"
        return "\n".join([f"- {item}" for item in items[:5]])
    
    def _format_food_trail(self, food_data: List) -> str:
        """Format food trail for prompt."""
        if not food_data:
            return "- Try local specialties during meals"
        tips = []
        for item in food_data[:5]:
            if isinstance(item, dict):
                tips.append(f"- {item.get('dish', 'Local dish')} at {item.get('area', 'local restaurants')}")
            else:
                tips.append(f"- {item}")
        return "\n".join(tips) if tips else "- Try local specialties during meals"
    
    async def _generate_planning_intelligence(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        budget: int,
        interests: List[str],
        weather_data: Dict,
        city_data: Dict,
    ) -> Dict[str, Any]:
        """Generate planning intelligence BEFORE creating itinerary to optimize the plan."""
        try:
            # Build context
            weather_summary = weather_data.get('summary', '') if isinstance(weather_data, dict) else ''
            famous_food = [f.get("name", "") for f in city_data.get("famous_food", [])[:5] if f.get("name")]
            events = [e.get("name", "") for e in city_data.get("festivals_events", [])[:3] if e.get("name")]
            
            prompt = f"""You are a travel planning expert. Analyze this trip and provide planning intelligence to create an OPTIMIZED itinerary.

DESTINATION: {destination}
DATES: {start_date} to {end_date}
BUDGET: ₹{budget:,} per person
INTERESTS: {', '.join(interests) if interests else 'General sightseeing'}
WEATHER: {weather_summary}
FAMOUS FOODS: {', '.join(famous_food) if famous_food else 'Local cuisine'}
EVENTS: {', '.join(events) if events else 'None scheduled'}

Provide planning intelligence as JSON:
{{
    "routeOptimization": "One sentence on how to group/order attractions geographically",
    "crowdTiming": [
        {{"place": "Main Temple", "bestTime": "6-8 AM", "avoidTime": "12-2 PM, 5-7 PM"}},
        {{"place": "Museum", "bestTime": "10 AM - 12 PM", "avoidTime": "3-5 PM weekends"}}
    ],
    "weatherRouting": [
        {{"day": 1, "suggestion": "Start early, avoid outdoor 12-3 PM due to heat"}},
        {{"day": 2, "suggestion": "Good for outdoor activities"}}
    ],
    "budgetGuidance": "Brief budget assessment - is it sufficient, tight, or generous",
    "ticketingNotes": "Brief note on any advance booking needed",
    "transitRecommendations": "Best local transport options with approximate costs",
    "etiquetteTips": ["tip1", "tip2", "tip3"],
    "safetyTips": ["safety tip1", "safety tip2"],
    "foodTrail": [
        {{"dish": "Famous dish 1", "area": "Best area to try it"}},
        {{"dish": "Famous dish 2", "area": "Best area to try it"}}
    ]
}}

Return ONLY valid JSON. Be specific to {destination}."""

            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a travel planning expert. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500,
            )

            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1].strip()
                    if content.startswith("json"):
                        content = content[4:].strip()
            
            if not content.startswith("{"):
                start_idx = content.find("{")
                if start_idx != -1:
                    content = content[start_idx:]
            
            if not content.endswith("}"):
                end_idx = content.rfind("}")
                if end_idx != -1:
                    content = content[:end_idx+1]
            
            parsed = json.loads(content)
            print(f"   ✓ [Planning Intelligence] Generated successfully")
            return parsed
            
        except Exception as e:
            print(f"⚠️ [Orchestrator] Planning intelligence generation failed: {e}")
            # Return helpful defaults
            return {
                "routeOptimization": f"Group nearby attractions in {destination} to minimize travel",
                "crowdTiming": [
                    {"place": "Popular temples", "bestTime": "Early morning 6-8 AM", "avoidTime": "12-2 PM, 5-7 PM"}
                ],
                "weatherRouting": [
                    {"day": 1, "suggestion": "Avoid outdoor activities during midday heat"}
                ],
                "budgetGuidance": "Budget appears reasonable for this trip",
                "ticketingNotes": "Check advance booking for popular attractions",
                "transitRecommendations": "Use local auto-rickshaws (₹50-150) or cabs (₹200-500)",
                "etiquetteTips": [
                    "Dress modestly at religious sites",
                    "Remove footwear before entering temples",
                    "Respect photography restrictions"
                ],
                "safetyTips": [
                    "Keep valuables secure in crowds",
                    "Use registered transport services"
                ],
                "foodTrail": [
                    {"dish": "Local specialty", "area": "Near main attractions"}
                ]
            }
    
    async def _enrich_places_parallel(
        self,
        itinerary: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """Enrich all places with real data in parallel using specialized agents."""
        
        # Collect all unique places
        places_to_enrich = []
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("place") and not slot.get("isMeal"):
                    place_name = slot["place"].get("name", "")
                    if place_name and place_name not in [p["name"] for p in places_to_enrich]:
                        places_to_enrich.append({
                            "name": place_name,
                            "day": day.get("day"),
                            "slot": slot
                        })
        
        print(f"   Enriching {len(places_to_enrich)} unique places...")
        
        # Create tasks for parallel enrichment
        async def enrich_single_place(place_info):
            place_name = place_info["name"]
            
            # Run all three agents in parallel for each place
            research_task = asyncio.create_task(
                self.place_research_agent.research_place(place_name, destination)
            )
            photo_task = asyncio.create_task(
                self.photo_review_agent.research_place(place_name, destination)
            )
            crowd_task = asyncio.create_task(
                self.place_research_agent.get_crowd_predictions(place_name, destination)
            )
            
            research_data, photo_data, crowd_data = await asyncio.gather(research_task, photo_task, crowd_task)
            
            return {
                "name": place_name,
                "research": research_data,
                "photos": photo_data,
                "crowd": crowd_data
            }
        
        # Run all place enrichments (with some parallelism limit)
        batch_size = 3  # Process 3 places at a time
        all_enriched = {}
        
        for i in range(0, len(places_to_enrich), batch_size):
            batch = places_to_enrich[i:i+batch_size]
            tasks = [enrich_single_place(p) for p in batch]
            results = await asyncio.gather(*tasks)
            
            for r in results:
                all_enriched[r["name"]] = r
        
        # Apply enrichment to itinerary
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("place") and not slot.get("isMeal"):
                    place_name = slot["place"].get("name", "")
                    if place_name in all_enriched:
                        enriched = all_enriched[place_name]
                        
                        # Merge research data
                        research = enriched.get("research", {})
                        slot["place"]["practicalInfo"] = {
                            "typicalDuration": research.get("visit_duration"),
                            "openingHours": research.get("opening_hours"),
                            "ticketInfo": research.get("ticket_info"),
                            "bestTimeToVisit": research.get("best_time_to_visit"),
                            "dressCode": research.get("dress_code"),
                            "importantTips": research.get("practical_tips", []),
                            "warnings": research.get("warnings", []),
                            "specialEvents": research.get("special_events", []),
                            "crowdPredictions": enriched.get("crowd"),
                        }
                        
                        # Also add crowd predictions to the slot itself for easy access
                        slot["crowdPredictions"] = enriched.get("crowd")
                        
                        # Merge photo data
                        photos = enriched.get("photos", {})
                        slot["place"]["images"] = photos.get("images", [])
                        slot["place"]["rating"] = photos.get("rating")
                        slot["place"]["totalReviews"] = photos.get("total_reviews")
                        slot["place"]["reviewSummary"] = photos.get("review_summary")
                        slot["place"]["googleMapsUrl"] = photos.get("google_maps_url")
                        slot["place"]["address"] = photos.get("address")
                        slot["place"]["crowdPredictions"] = enriched.get("crowd")
        
        print(f"   ✓ Enriched {len(all_enriched)} places with real data")
        
        return itinerary
    
    async def _enrich_meals_parallel(
        self,
        itinerary: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """Enrich meal slots with real restaurant recommendations."""
        
        # Collect all meal slots
        meal_slots = []
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("isMeal"):
                    meal_slots.append({
                        "day": day.get("day"),
                        "slot": slot,
                        "meal_type": slot.get("mealType", "lunch")
                    })
        
        print(f"   Finding restaurants for {len(meal_slots)} meals...")
        
        # Create restaurant finding tasks
        async def find_restaurant_for_meal(meal_info):
            restaurant = await self.dining_agent.find_meal_restaurant(
                location=destination,
                meal_type=meal_info["meal_type"]
            )
            return {
                "day": meal_info["day"],
                "meal_type": meal_info["meal_type"],
                "restaurant": restaurant
            }
        
        # Process meals in batches
        batch_size = 4
        all_restaurants = []
        
        for i in range(0, len(meal_slots), batch_size):
            batch = meal_slots[i:i+batch_size]
            tasks = [find_restaurant_for_meal(m) for m in batch]
            results = await asyncio.gather(*tasks)
            all_restaurants.extend(results)
        
        # Apply restaurants to itinerary
        restaurant_map = {}
        for r in all_restaurants:
            key = f"{r['day']}_{r['meal_type']}"
            restaurant_map[key] = r["restaurant"]
        
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("isMeal"):
                    key = f"{day.get('day')}_{slot.get('mealType', 'lunch')}"
                    if key in restaurant_map and restaurant_map[key]:
                        rest = restaurant_map[key]
                        slot["restaurant"] = {
                            "name": rest.get("name"),
                            "cuisine": rest.get("cuisine"),
                            "rating": rest.get("rating"),
                            "totalReviews": rest.get("total_reviews"),
                            "priceLevel": rest.get("price_level"),
                            "address": rest.get("address"),
                            "phone": rest.get("phone"),
                            "website": rest.get("website"),
                            "googleMapsUrl": rest.get("google_maps_url"),
                            "images": rest.get("images", []),
                            "mustTry": rest.get("must_try", []),
                            "reviewSnippet": rest.get("review_snippet"),
                        }
        
        restaurants_added = sum(1 for r in all_restaurants if r["restaurant"])
        print(f"   ✓ Added {restaurants_added} real restaurant recommendations")
        
        return itinerary
    
    def _count_enriched_places(self, itinerary: Dict) -> int:
        """Count places with enriched data."""
        count = 0
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("place", {}).get("images"):
                    count += 1
        return count
    
    def _count_meals_with_restaurants(self, itinerary: Dict) -> int:
        """Count meals with restaurant recommendations."""
        count = 0
        for day in itinerary.get("days", []):
            for slot in day.get("schedule", []):
                if slot.get("isMeal") and slot.get("restaurant"):
                    count += 1
        return count
    
    # ===== Chat/Replanning Interface =====
    
    async def chat(
        self,
        message: str,
        current_itinerary: Dict[str, Any],
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Smart Agent-Router Chat System.
        Detects intent and routes to appropriate agents or performs actions.
        """
        print(f"\n💬 [Orchestrator] Smart Chat Processing: '{message[:50]}...'")
        
        # Step 1: Detect intent and required action
        intent = await self._detect_chat_intent(message, current_itinerary)
        print(f"   Intent: {intent.get('intent_type')} | Action: {intent.get('action')}")
        
        result = {
            "success": True,
            "reply": "",
            "is_modification_request": False,
            "should_replan": False,
            "action": None,  # Frontend action command
            "action_data": None,  # Data for the action
            "agent_used": None,
        }
        
        intent_type = intent.get("intent_type", "general_chat")
        
        try:
            # Route to appropriate handler based on intent
            if intent_type == "navigation":
                result = await self._handle_navigation(intent, result)
                
            elif intent_type == "modify_itinerary":
                result = await self._handle_modify_itinerary(message, current_itinerary, intent, result)
                
            elif intent_type == "weather_query":
                result = await self._handle_weather_query(current_itinerary, intent, result)
                
            elif intent_type == "place_info":
                result = await self._handle_place_query(current_itinerary, intent, result)
                
            elif intent_type == "restaurant_query":
                result = await self._handle_restaurant_query(current_itinerary, intent, result)
                
            elif intent_type == "city_info":
                result = await self._handle_city_query(current_itinerary, intent, result)
                
            elif intent_type == "booking_action":
                result = await self._handle_booking_action(intent, result)
                
            elif intent_type == "itinerary_question":
                result = await self._handle_itinerary_question(message, current_itinerary, chat_history, result)
                
            else:
                # General chat - use replanning agent's chat
                chat_result = await self.replanning_agent.chat(message, current_itinerary, chat_history)
                result["reply"] = chat_result.get("reply", "I'm not sure how to help with that.")
                result["agent_used"] = "replanning_agent"
                
        except Exception as e:
            print(f"   ✗ Chat error: {e}")
            result["reply"] = "I encountered an error. Please try again."
            result["success"] = False
            
        return result
    
    async def _detect_chat_intent(self, message: str, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        """Detect user intent from chat message using LLM."""
        
        destination = itinerary.get("destination", "the destination")
        
        prompt = f"""Analyze this user message and detect the intent. User is on a travel planning website with an itinerary for {destination}.

User Message: "{message}"

Classify into ONE of these intent types:
1. "navigation" - User wants to go to a section/page (about, contact, home, booking, itinerary form, etc.)
2. "modify_itinerary" - User wants to change/add/remove something from their itinerary
3. "weather_query" - User asks about weather at destination
4. "place_info" - User asks about a specific place, attraction, best time to visit, crowd info
5. "restaurant_query" - User asks about restaurants, food recommendations, where to eat
6. "city_info" - User asks about the city, famous things, local tips, what's special
7. "booking_action" - User wants to book flights, hotels, tickets, or see booking options
8. "itinerary_question" - User has a question about their current itinerary
9. "general_chat" - General conversation, greetings, or unclear intent

Return JSON:
{{
    "intent_type": "one of the above",
    "action": "specific action if applicable (e.g., 'scroll_to_about', 'open_flight_booking')",
    "target": "what user is asking about (place name, day number, etc.)",
    "details": "additional context extracted from message"
}}"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
            )
            
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            if not content.startswith("{"):
                content = content[content.find("{"):]
            if not content.endswith("}"):
                content = content[:content.rfind("}")+1]
                
            return json.loads(content)
            
        except Exception as e:
            print(f"   ⚠️ Intent detection failed: {e}")
            return {"intent_type": "general_chat", "action": None, "target": None, "details": None}
    
    async def _handle_navigation(self, intent: Dict, result: Dict) -> Dict:
        """Handle navigation requests - scrolling to sections, opening pages."""
        action = intent.get("action", "").lower()
        target = intent.get("target", "").lower()
        details = intent.get("details", "").lower()
        
        # Determine navigation action
        nav_mapping = {
            "about": {"action": "scroll_to_section", "data": {"section": "about"}},
            "contact": {"action": "scroll_to_section", "data": {"section": "contact"}},
            "home": {"action": "scroll_to_section", "data": {"section": "hero"}},
            "top": {"action": "scroll_to_section", "data": {"section": "hero"}},
            "form": {"action": "scroll_to_section", "data": {"section": "itinerary-form"}},
            "plan": {"action": "scroll_to_section", "data": {"section": "itinerary-form"}},
            "itinerary": {"action": "scroll_to_section", "data": {"section": "itinerary-result"}},
            "result": {"action": "scroll_to_section", "data": {"section": "itinerary-result"}},
            "weather": {"action": "scroll_to_section", "data": {"section": "weather"}},
            "highlights": {"action": "scroll_to_section", "data": {"section": "city-highlights"}},
            "food": {"action": "scroll_to_section", "data": {"section": "famous-food"}},
            "restaurants": {"action": "scroll_to_section", "data": {"section": "restaurants"}},
        }
        
        # Find matching navigation
        combined = f"{action} {target} {details}"
        nav_action = None
        
        for key, nav in nav_mapping.items():
            if key in combined:
                nav_action = nav
                break
        
        if nav_action:
            result["action"] = nav_action["action"]
            result["action_data"] = nav_action["data"]
            result["reply"] = f"Taking you to the {nav_action['data']['section'].replace('-', ' ').replace('_', ' ')} section! 🚀"
        else:
            result["reply"] = "I'm not sure where you want to go. You can ask me to go to: About, Contact, Home, Itinerary Form, Weather, Highlights, or Food sections."
        
        result["agent_used"] = "navigation_handler"
        return result
    
    async def _handle_modify_itinerary(self, message: str, itinerary: Dict, intent: Dict, result: Dict) -> Dict:
        """Handle itinerary modification requests."""
        
        # Process modification via replanning agent
        mod_result = await self.replanning_agent.process_modification(itinerary, message)
        
        if mod_result.get("success"):
            # Re-enrich the modified itinerary
            destination = itinerary.get("destination")
            if destination and mod_result.get("modified_itinerary"):
                mod_result["modified_itinerary"] = await self._enrich_places_parallel(
                    mod_result["modified_itinerary"],
                    destination
                )
            
            result["reply"] = f"✅ I've updated your itinerary! Changes made:\n" + "\n".join([f"• {c}" for c in mod_result.get("changes_made", ["Itinerary updated"])])
            result["is_modification_request"] = True
            result["should_replan"] = True
            result["action"] = "update_itinerary"
            result["action_data"] = {"itinerary": mod_result.get("modified_itinerary")}
        else:
            result["reply"] = "I couldn't make that change. Can you please be more specific about what you'd like to modify?"
        
        result["agent_used"] = "replanning_agent"
        return result
    
    async def _handle_weather_query(self, itinerary: Dict, intent: Dict, result: Dict) -> Dict:
        """Handle weather-related queries using Weather Agent."""
        destination = itinerary.get("destination", "")
        start_date = itinerary.get("startDate", "")
        end_date = itinerary.get("endDate", "")
        
        if destination:
            weather_data = await self.weather_agent.research(destination, str(start_date), str(end_date))
            
            if weather_data.get("success"):
                summary = weather_data.get("summary", "Weather data available")
                recommendations = weather_data.get("recommendations", [])
                
                reply = f"🌤️ **Weather for {destination}:**\n\n{summary}\n\n"
                if recommendations:
                    reply += "**Recommendations:**\n" + "\n".join([f"• {r}" for r in recommendations[:3]])
                
                result["reply"] = reply
                result["action"] = "scroll_to_section"
                result["action_data"] = {"section": "weather"}
            else:
                result["reply"] = f"I couldn't fetch weather data for {destination} right now. Please check a weather website for accurate information."
        else:
            result["reply"] = "Please generate an itinerary first so I can check the weather for your destination!"
        
        result["agent_used"] = "weather_agent"
        return result
    
    async def _handle_place_query(self, itinerary: Dict, intent: Dict, result: Dict) -> Dict:
        """Handle place-related queries using Place Research Agent."""
        target = intent.get("target", "")
        destination = itinerary.get("destination", "")
        
        if target and destination:
            # Research the place
            place_data = await self.place_research_agent.research_place(target, destination)
            crowd_data = await self.place_research_agent.get_crowd_predictions(target, destination)
            
            reply = f"📍 **{target}**\n\n"
            
            if place_data.get("visit_duration"):
                reply += f"⏱️ **Typical Duration:** {place_data['visit_duration']}\n"
            if place_data.get("best_time_to_visit"):
                reply += f"🌟 **Best Time to Visit:** {place_data['best_time_to_visit']}\n"
            if place_data.get("ticket_info"):
                reply += f"🎫 **Tickets:** {place_data['ticket_info']}\n"
            if place_data.get("dress_code"):
                reply += f"👔 **Dress Code:** {place_data['dress_code']}\n"
            
            if crowd_data.get("bestTimes"):
                reply += f"\n👥 **Crowd Tips:**\n"
                reply += f"• Best times: {', '.join(crowd_data['bestTimes'][:2])}\n"
                if crowd_data.get("recommendations"):
                    reply += f"• {crowd_data['recommendations'][0]}\n"
            
            if place_data.get("practical_tips"):
                reply += f"\n💡 **Tips:**\n" + "\n".join([f"• {t}" for t in place_data['practical_tips'][:2]])
            
            result["reply"] = reply if len(reply) > 50 else f"I found some information about {target} but details are limited. It's a popular attraction in {destination}!"
        else:
            result["reply"] = "Which place would you like to know about? Please specify the attraction name."
        
        result["agent_used"] = "place_research_agent"
        return result
    
    async def _handle_restaurant_query(self, itinerary: Dict, intent: Dict, result: Dict) -> Dict:
        """Handle restaurant queries using Dining Agent."""
        destination = itinerary.get("destination", "")
        target = intent.get("target", "")
        details = intent.get("details", "")
        
        # Determine meal type from query
        meal_type = "lunch"  # default
        if "breakfast" in details.lower():
            meal_type = "breakfast"
        elif "dinner" in details.lower():
            meal_type = "dinner"
        elif "snack" in details.lower() or "tea" in details.lower():
            meal_type = "snack"
        
        if destination:
            restaurant = await self.dining_agent.find_meal_restaurant(destination, meal_type)
            
            if restaurant:
                reply = f"🍽️ **Restaurant Recommendation for {meal_type.title()}:**\n\n"
                reply += f"**{restaurant.get('name', 'Local Restaurant')}**\n"
                if restaurant.get("cuisine"):
                    reply += f"🍴 Cuisine: {restaurant['cuisine']}\n"
                if restaurant.get("rating"):
                    reply += f"⭐ Rating: {restaurant['rating']}/5\n"
                if restaurant.get("priceLevel"):
                    reply += f"💰 Price: {restaurant['priceLevel']}\n"
                if restaurant.get("address"):
                    reply += f"📍 {restaurant['address']}\n"
                if restaurant.get("mustTry"):
                    reply += f"\n✨ Must Try: {', '.join(restaurant['mustTry'][:3])}"
                
                result["reply"] = reply
                result["action"] = "scroll_to_section"
                result["action_data"] = {"section": "restaurants"}
            else:
                result["reply"] = f"I couldn't find specific restaurant recommendations right now. {destination} has many great local eateries - I suggest exploring near your attractions!"
        else:
            result["reply"] = "Please generate an itinerary first so I can recommend restaurants for your destination!"
        
        result["agent_used"] = "dining_agent"
        return result
    
    async def _handle_city_query(self, itinerary: Dict, intent: Dict, result: Dict) -> Dict:
        """Handle city-related queries using City Explorer Agent."""
        destination = itinerary.get("destination", "")
        target = intent.get("target", "").lower()
        
        if destination:
            city_data = await self.city_explorer_agent.explore_city(destination, [])
            
            reply = f"🏙️ **About {destination}:**\n\n"
            
            # Determine what aspect user is asking about
            if "food" in target or "eat" in target or "dish" in target:
                foods = city_data.get("famous_food", [])[:4]
                if foods:
                    reply = f"🍲 **Famous Food in {destination}:**\n\n"
                    for f in foods:
                        reply += f"• **{f.get('name', 'Local Dish')}**: {f.get('description', '')[:100]}\n"
                result["action"] = "scroll_to_section"
                result["action_data"] = {"section": "famous-food"}
                
            elif "shop" in target or "buy" in target or "market" in target:
                shops = city_data.get("shopping_areas", [])[:3]
                if shops:
                    reply = f"🛍️ **Shopping in {destination}:**\n\n"
                    for s in shops:
                        reply += f"• **{s.get('name', 'Market')}**: {s.get('description', '')[:80]}\n"
                        
            elif "tip" in target or "advice" in target:
                tips = city_data.get("local_tips", [])[:5]
                if tips:
                    reply = f"💡 **Local Tips for {destination}:**\n\n" + "\n".join([f"• {t}" for t in tips])
                    
            elif "festival" in target or "event" in target:
                events = city_data.get("festivals_events", [])[:3]
                if events:
                    reply = f"🎉 **Events in {destination}:**\n\n"
                    for e in events:
                        reply += f"• **{e.get('name', 'Event')}**: {e.get('description', '')[:80]}\n"
            else:
                # General city info
                if city_data.get("famous_food"):
                    reply += f"🍲 Famous for: {', '.join([f.get('name', '') for f in city_data['famous_food'][:3]])}\n"
                if city_data.get("local_tips"):
                    reply += f"\n💡 Quick Tips:\n" + "\n".join([f"• {t}" for t in city_data['local_tips'][:2]])
                    
                result["action"] = "scroll_to_section"
                result["action_data"] = {"section": "city-highlights"}
            
            result["reply"] = reply
        else:
            result["reply"] = "Please generate an itinerary first so I can tell you about your destination!"
        
        result["agent_used"] = "city_explorer_agent"
        return result
    
    async def _handle_booking_action(self, intent: Dict, result: Dict) -> Dict:
        """Handle booking-related actions."""
        target = intent.get("target", "").lower()
        details = intent.get("details", "").lower()
        combined = f"{target} {details}"
        
        if "flight" in combined:
            result["action"] = "open_external"
            result["action_data"] = {"url": "https://www.makemytrip.com/flights/", "type": "flight_booking"}
            result["reply"] = "🛫 Opening flight booking for you! I'm redirecting you to a flight booking website."
            
        elif "hotel" in combined or "stay" in combined or "accommodation" in combined:
            result["action"] = "open_external"
            result["action_data"] = {"url": "https://www.makemytrip.com/hotels/", "type": "hotel_booking"}
            result["reply"] = "🏨 Opening hotel booking for you! I'm redirecting you to find great stays."
            
        elif "train" in combined:
            result["action"] = "open_external"
            result["action_data"] = {"url": "https://www.irctc.co.in/", "type": "train_booking"}
            result["reply"] = "🚂 Opening IRCTC for train booking! You can book your train tickets there."
            
        elif "bus" in combined:
            result["action"] = "open_external"
            result["action_data"] = {"url": "https://www.redbus.in/", "type": "bus_booking"}
            result["reply"] = "🚌 Opening RedBus for you! Book your bus tickets there."
            
        elif "cab" in combined or "taxi" in combined:
            result["action"] = "open_external"
            result["action_data"] = {"url": "https://www.olacabs.com/", "type": "cab_booking"}
            result["reply"] = "🚕 For cabs, I recommend using Ola or Uber apps on your phone for best rates!"
            
        else:
            result["reply"] = "What would you like to book? I can help with:\n• ✈️ Flights\n• 🏨 Hotels\n• 🚂 Trains\n• 🚌 Buses\n\nJust tell me which one!"
        
        result["agent_used"] = "booking_handler"
        return result
    
    async def _handle_itinerary_question(self, message: str, itinerary: Dict, chat_history: List, result: Dict) -> Dict:
        """Handle questions about the current itinerary."""
        
        # Use LLM to answer based on itinerary context
        itinerary_summary = self._get_itinerary_summary(itinerary)
        
        prompt = f"""Answer this question about the user's travel itinerary.

ITINERARY:
{itinerary_summary}

USER QUESTION: "{message}"

Provide a helpful, concise answer based on the itinerary data. If the answer isn't in the itinerary, say so and suggest alternatives. Use emojis to make it friendly. All costs in ₹."""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant. Answer questions about the user's itinerary concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            result["reply"] = response.choices[0].message.content.strip()
            result["action"] = "scroll_to_section"
            result["action_data"] = {"section": "itinerary-result"}
            
        except Exception as e:
            result["reply"] = "I couldn't process your question. Please try asking in a different way!"
        
        result["agent_used"] = "itinerary_qa"
        return result
    
    def _get_itinerary_summary(self, itinerary: Dict) -> str:
        """Get a summary of the itinerary for LLM context."""
        summary = f"Destination: {itinerary.get('destination', 'Unknown')}\n"
        summary += f"Dates: {itinerary.get('startDate', '')} to {itinerary.get('endDate', '')}\n\n"
        
        for day in itinerary.get("days", []):
            summary += f"Day {day.get('day')} ({day.get('date', '')}) - {day.get('theme', '')}:\n"
            for slot in day.get("schedule", []):
                time = slot.get("time", "")
                activity = slot.get("activity", "")
                summary += f"  {time}: {activity}\n"
            summary += "\n"
        
        return summary[:3000]  # Limit for token size
    
    async def modify_itinerary(
        self,
        current_itinerary: Dict[str, Any],
        modification_request: str
    ) -> Dict[str, Any]:
        """
        Process an itinerary modification request.
        Delegates to Replanning Agent, then re-enriches affected places.
        """
        print(f"\n{'='*60}")
        print(f"✏️ [Orchestrator] Processing Modification Request")
        print(f"   Request: '{modification_request[:50]}...'")
        print(f"{'='*60}\n")
        
        # Get modification from replanning agent
        result = await self.replanning_agent.process_modification(
            current_itinerary,
            modification_request
        )
        
        if result.get("success") and result.get("modified_itinerary"):
            # Re-enrich any new places
            destination = result["modified_itinerary"].get("destination")
            if destination:
                print("🔄 [Orchestrator] Re-enriching modified itinerary...")
                result["modified_itinerary"] = await self._enrich_places_parallel(
                    result["modified_itinerary"],
                    destination
                )
                result["modified_itinerary"] = await self._enrich_meals_parallel(
                    result["modified_itinerary"],
                    destination
                )
        
        return result
