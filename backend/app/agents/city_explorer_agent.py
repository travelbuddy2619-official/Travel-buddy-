"""
City Explorer Agent - Specialized agent for city-level information
Researches famous food, local specialties, festivals, events, and hidden gems
Uses LLM to summarize raw search results into organized, readable content
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import httpx
import json
import os
from groq import AsyncGroq

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_PLACES_URL = "https://google.serper.dev/places"


class CityExplorerAgent:
    """Agent specialized in researching city-level information and local highlights."""
    
    name = "City Explorer Agent"
    description = "Researches famous food, local specialties, festivals, and city highlights"
    
    def __init__(self, serper_api_key: str, groq_api_key: str = None, rapidapi_key: str = None):
        self.serper_api_key = serper_api_key
        self.rapidapi_key = rapidapi_key
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_client = AsyncGroq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
    
    async def explore_city(self, city: str, travel_dates: List[str] = None) -> Dict[str, Any]:
        """
        Comprehensive city exploration - food, events, local tips.
        All results are summarized by LLM for clean, readable output.
        """
        print(f"🏙️ [City Explorer Agent] Exploring {city}...")
        
        result = {
            "city": city,
            "famous_food": [],
            "famous_restaurants": [],
            "local_specialties": [],
            "shopping_areas": [],
            "festivals_events": [],
            "local_tips": [],
            "hidden_gems": [],
            "safety_info": None,
            "transport_tips": [],
        }
        
        try:
            # 1. Famous food of the city - search and summarize
            famous_food = await self._research_famous_food(city)
            result["famous_food"] = famous_food
            
            # 2. Famous restaurants - use PLACES API for real data
            famous_restaurants = await self._research_famous_restaurants(city)
            result["famous_restaurants"] = famous_restaurants
            
            # 3. Local specialties (not just food)
            local_specialties = await self._research_local_specialties(city)
            result["local_specialties"] = local_specialties
            
            # 4. Shopping areas - summarized
            shopping = await self._research_shopping(city)
            result["shopping_areas"] = shopping
            
            # 5. Festivals/events during travel dates
            if travel_dates:
                events = await self._research_events(city, travel_dates)
                result["festivals_events"] = events
            
            # 6. Local tips and transport - summarized
            tips = await self._research_local_tips(city)
            result["local_tips"] = tips.get("tips", [])
            result["transport_tips"] = tips.get("transport", [])
            result["safety_info"] = tips.get("safety")
            
            # 7. Hidden gems - summarized
            gems = await self._research_hidden_gems(city)
            result["hidden_gems"] = gems
            
            print(f"✓ [City Explorer Agent] Completed exploration of {city}")
            
        except Exception as e:
            print(f"✗ [City Explorer Agent] Error exploring {city}: {e}")
        
        return result
    
    async def _summarize_with_llm(self, raw_data: str, prompt: str) -> str:
        """Use Groq LLM to summarize raw search data into clean text."""
        if not self.groq_client:
            return raw_data[:300]  # Fallback if no LLM
        
        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant. Summarize information concisely and accurately. Be specific with names, places, and details. Keep responses short but complete."},
                    {"role": "user", "content": f"{prompt}\n\nRaw data:\n{raw_data}"}
                ],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ LLM summarization error: {e}")
            return raw_data[:300]
    
    async def _research_famous_food(self, city: str) -> List[Dict[str, Any]]:
        """Research famous food dishes SPECIFIC to this city, like a human searching on Google."""
        foods = []
        
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                # Multiple searches like a human would do
                search_queries = [
                    f"what are the famous food dishes of {city}",
                    f"{city} famous food must try dishes",
                    f"best local food to eat in {city} India",
                    f"{city} street food specialties",
                ]
                
                raw_snippets = []
                
                for query in search_queries[:2]:  # Use first 2 queries
                    resp = await client.post(
                        SERPER_SEARCH_URL,
                        headers=self.headers,
                        json={
                            "q": query,
                            "num": 6,
                            "gl": "in",
                            "hl": "en"
                        }
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    
                    # Check answer box first - Google's direct answer
                    if data.get("answerBox"):
                        answer = data["answerBox"].get("snippet") or data["answerBox"].get("answer")
                        if answer:
                            raw_snippets.append(f"Google Answer: {answer}")
                    
                    # Knowledge graph
                    if data.get("knowledgeGraph"):
                        kg = data["knowledgeGraph"]
                        if kg.get("description"):
                            raw_snippets.append(f"Knowledge: {kg['description']}")
                    
                    # Organic results
                    for item in data.get("organic", [])[:4]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        raw_snippets.append(f"{title}: {snippet}")
                
                # Use LLM to extract and summarize famous foods
                if raw_snippets and self.groq_client:
                    raw_text = "\n".join(raw_snippets)
                    
                    prompt = f"""You are researching famous food of {city} city in India.

From the Google search results below, extract 5-6 specific famous dishes/food items that {city} is known for.

For EACH dish, provide:
- name: The exact dish name (e.g., "Tirupati Laddu", "Pulihora", "Pesarattu")
- description: A clear 2-3 sentence description explaining what it is, its taste, and why it's famous in {city}

IMPORTANT:
- Be SPECIFIC to {city} - only include foods that are genuinely famous in THIS city
- Include local street food, traditional dishes, temple prasadam (if religious city), and regional specialties
- Don't include generic Indian food unless {city} is specifically known for it

Return ONLY a valid JSON array:
[{{"name": "Dish Name", "description": "Clear description of the dish"}}]

Search Results:
{raw_text}"""
                    
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are a food expert who extracts accurate local food information. Return only valid JSON arrays."},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=800,
                            temperature=0.3
                        )
                        result_text = response.choices[0].message.content.strip()
                        
                        # Parse JSON from response
                        if "[" in result_text:
                            json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                            foods = json.loads(json_str)
                            print(f"   ✓ Found {len(foods)} famous food items for {city}")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Food JSON parse error: {e}")
                    except Exception as e:
                        print(f"⚠️ Food LLM error: {e}")
                
                # Get images for the foods - search specifically for each dish
                if foods:
                    print(f"   📷 Fetching images for {len(foods)} dishes...")
                    for food in foods[:5]:
                        try:
                            # Search for specific dish image
                            img_resp = await client.post(
                                SERPER_IMAGES_URL,
                                headers=self.headers,
                                json={
                                    "q": f"{food['name']} {city} food dish",
                                    "num": 2,
                                    "gl": "in"
                                }
                            )
                            if img_resp.status_code == 200:
                                img_data = img_resp.json()
                                images = img_data.get("images", [])
                                if images:
                                    # Get the first good image
                                    food["image"] = images[0].get("imageUrl")
                        except Exception as img_err:
                            print(f"   ⚠️ Image fetch error for {food.get('name')}: {img_err}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Food search error: {e}")
                import traceback
                traceback.print_exc()
        
        return foods[:6]
    
    async def _research_famous_restaurants(self, city: str) -> List[Dict[str, Any]]:
        """Research famous/iconic restaurants using Serper Places API for real data."""
        restaurants = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Use Places API for real restaurant data
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.headers,
                    json={
                        "q": f"famous restaurants in {city}",
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                for place in data.get("places", [])[:5]:
                    restaurant = {
                        "name": place.get("title", ""),
                        "address": place.get("address", ""),
                        "rating": place.get("rating"),
                        "totalReviews": place.get("reviewsCount") or place.get("reviews"),
                        "priceLevel": place.get("priceLevel", ""),
                        "category": place.get("category", "Restaurant"),
                        "openingHours": None,
                        "phone": place.get("phoneNumber"),
                        "website": place.get("website"),
                    }
                    
                    # Get opening hours if available
                    if place.get("openingHours"):
                        hours = place["openingHours"]
                        if isinstance(hours, list) and hours:
                            restaurant["openingHours"] = hours[0] if len(hours) == 1 else f"{hours[0]} - {hours[-1]}"
                        elif isinstance(hours, str):
                            restaurant["openingHours"] = hours
                    
                    # Get CID for Google Maps link
                    if place.get("cid"):
                        restaurant["googleMapsUrl"] = f"https://www.google.com/maps?cid={place['cid']}"
                    elif place.get("latitude") and place.get("longitude"):
                        restaurant["googleMapsUrl"] = f"https://www.google.com/maps?q={place['latitude']},{place['longitude']}"
                    
                    restaurants.append(restaurant)
                
                # If no places found, search and use LLM to extract
                if not restaurants:
                    resp = await client.post(
                        SERPER_SEARCH_URL,
                        headers=self.headers,
                        json={
                            "q": f"best iconic famous restaurants in {city} where to eat",
                            "num": 6,
                            "gl": "in"
                        }
                    )
                    resp.raise_for_status()
                    search_data = resp.json()
                    
                    raw_snippets = []
                    for item in search_data.get("organic", [])[:5]:
                        raw_snippets.append(f"{item.get('title', '')}: {item.get('snippet', '')}")
                    
                    if raw_snippets and self.groq_client:
                        prompt = f"""From these search results about restaurants in {city}, extract 3-4 specific restaurant names.
Return ONLY a JSON array like:
[{{"name": "Restaurant Name", "description": "Brief description of what they serve"}}]"""
                        
                        try:
                            response = await self.groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "Extract restaurant information and return valid JSON only."},
                                    {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                                ],
                                max_tokens=400,
                                temperature=0.2
                            )
                            result_text = response.choices[0].message.content.strip()
                            if "[" in result_text:
                                json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                                restaurants = json.loads(json_str)
                        except Exception as e:
                            print(f"⚠️ Restaurant LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Restaurant search error: {e}")
        
        return restaurants[:4]
    
    async def _research_local_specialties(self, city: str) -> List[Dict[str, str]]:
        """Research local specialties (handicrafts, arts, etc.) specific to this city."""
        specialties = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={
                        "q": f"what is {city} famous for shopping souvenirs handicrafts local products to buy",
                        "num": 6,
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                raw_snippets = []
                for item in data.get("organic", [])[:5]:
                    snippet = item.get("snippet", "")
                    if city.lower() in snippet.lower():
                        raw_snippets.append(snippet)
                
                if raw_snippets and self.groq_client:
                    prompt = f"""From these search results, extract 2-3 things that {city} is famous for (handicrafts, souvenirs, local products).
Return ONLY a JSON array like:
[{{"item": "Item Name", "description": "Brief description"}}]"""
                    
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Extract local specialty information and return valid JSON only."},
                                {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                            ],
                            max_tokens=300,
                            temperature=0.2
                        )
                        result_text = response.choices[0].message.content.strip()
                        if "[" in result_text:
                            json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                            specialties = json.loads(json_str)
                    except Exception as e:
                        print(f"⚠️ Specialties LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Specialties search error: {e}")
        
        return specialties[:3]
    
    async def _research_shopping(self, city: str) -> List[Dict[str, str]]:
        """Research famous shopping areas in this city using Places API."""
        shopping = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Use Places API for real shopping data
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.headers,
                    json={
                        "q": f"famous markets shopping in {city}",
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                for place in data.get("places", [])[:4]:
                    shop = {
                        "name": place.get("title", ""),
                        "address": place.get("address", ""),
                        "rating": place.get("rating"),
                        "category": place.get("category", "Shopping"),
                    }
                    if place.get("cid"):
                        shop["googleMapsUrl"] = f"https://www.google.com/maps?cid={place['cid']}"
                    shopping.append(shop)
                
                # If no places, fall back to search + LLM
                if not shopping:
                    resp = await client.post(
                        SERPER_SEARCH_URL,
                        headers=self.headers,
                        json={
                            "q": f"famous markets shopping areas in {city} where to shop",
                            "num": 5,
                            "gl": "in"
                        }
                    )
                    resp.raise_for_status()
                    search_data = resp.json()
                    
                    raw_snippets = []
                    for item in search_data.get("organic", [])[:4]:
                        snippet = item.get("snippet", "")
                        if city.lower() in snippet.lower():
                            raw_snippets.append(snippet)
                    
                    if raw_snippets and self.groq_client:
                        prompt = f"""From these results, extract 3 famous shopping places/markets in {city}.
Return ONLY a JSON array like:
[{{"name": "Market Name", "description": "What you can buy there"}}]"""
                        
                        try:
                            response = await self.groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "Extract shopping information and return valid JSON only."},
                                    {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                                ],
                                max_tokens=300,
                                temperature=0.2
                            )
                            result_text = response.choices[0].message.content.strip()
                            if "[" in result_text:
                                json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                                shopping = json.loads(json_str)
                        except Exception as e:
                            print(f"⚠️ Shopping LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Shopping search error: {e}")
        
        return shopping[:4]
    
    async def _research_events(self, city: str, dates: List[str]) -> List[Dict[str, str]]:
        """Research festivals and events happening during specific travel dates."""
        events = []
        
        if not dates:
            return events
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                from datetime import datetime
                
                # Parse dates to get month and year
                first_date = dates[0]
                last_date = dates[-1] if len(dates) > 1 else dates[0]
                
                start_obj = datetime.strptime(first_date, "%Y-%m-%d")
                end_obj = datetime.strptime(last_date, "%Y-%m-%d")
                
                month_name = start_obj.strftime("%B")
                year = start_obj.year
                
                # Format date range for search
                date_range = f"{start_obj.strftime('%d %B')} to {end_obj.strftime('%d %B %Y')}"
                
                # Search for events
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={
                        "q": f"festivals events in {city} {month_name} {year}",
                        "num": 8,
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                raw_snippets = []
                for item in data.get("organic", [])[:6]:
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    raw_snippets.append(f"{title}: {snippet}")
                
                if raw_snippets and self.groq_client:
                    prompt = f"""From these search results, extract any festivals or events happening in {city} during {month_name} {year}.
If no specific events are found for that period, mention major annual festivals of {city}.
Return ONLY a JSON array like:
[{{"name": "Festival/Event Name", "description": "Brief description", "period": "When it happens"}}]
Return empty array [] if nothing relevant found."""
                    
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Extract event information and return valid JSON only."},
                                {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                            ],
                            max_tokens=400,
                            temperature=0.2
                        )
                        result_text = response.choices[0].message.content.strip()
                        if "[" in result_text:
                            json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                            events = json.loads(json_str)
                    except Exception as e:
                        print(f"⚠️ Events LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Events search error: {e}")
        
        return events[:4]
    
    async def _research_local_tips(self, city: str) -> Dict[str, Any]:
        """Research local travel tips, transport, and safety info for this city."""
        result = {"tips": [], "transport": [], "safety": None}
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={
                        "q": f"{city} travel tips local transport how to get around tourist advice safety",
                        "num": 10,
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                raw_snippets = []
                for item in data.get("organic", [])[:8]:
                    snippet = item.get("snippet", "")
                    if city.lower() in snippet.lower():
                        raw_snippets.append(snippet)
                
                if raw_snippets and self.groq_client:
                    prompt = f"""From these search results about {city}, extract and organize:
1. transport: 2-3 tips about how to get around {city} (buses, autos, taxis, etc.)
2. tips: 2-3 general travel tips for visiting {city}
3. safety: Any safety advice (or null if none)

Return ONLY a JSON object like:
{{"transport": ["Tip 1", "Tip 2"], "tips": ["Tip 1", "Tip 2"], "safety": "Safety advice or null"}}"""
                    
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Extract travel tips and return valid JSON only."},
                                {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                            ],
                            max_tokens=400,
                            temperature=0.2
                        )
                        result_text = response.choices[0].message.content.strip()
                        if "{" in result_text:
                            json_str = result_text[result_text.find("{"):result_text.rfind("}")+1]
                            parsed = json.loads(json_str)
                            result["transport"] = parsed.get("transport", [])[:3]
                            result["tips"] = parsed.get("tips", [])[:3]
                            result["safety"] = parsed.get("safety")
                    except Exception as e:
                        print(f"⚠️ Tips LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Tips search error: {e}")
        
        return result
    
    async def _research_hidden_gems(self, city: str) -> List[Dict[str, str]]:
        """Research hidden gems and offbeat places in this city."""
        gems = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={
                        "q": f"{city} hidden gems offbeat places less known tourist spots locals recommend",
                        "num": 6,
                        "gl": "in"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                raw_snippets = []
                for item in data.get("organic", [])[:5]:
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    raw_snippets.append(f"{title}: {snippet}")
                
                if raw_snippets and self.groq_client:
                    prompt = f"""From these search results, extract 2-3 hidden gems or offbeat places to visit in {city}.
Return ONLY a JSON array like:
[{{"name": "Place Name", "description": "Why it's special and worth visiting"}}]"""
                    
                    try:
                        response = await self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Extract hidden gem information and return valid JSON only."},
                                {"role": "user", "content": f"{prompt}\n\nRaw data:\n" + "\n".join(raw_snippets)}
                            ],
                            max_tokens=300,
                            temperature=0.2
                        )
                        result_text = response.choices[0].message.content.strip()
                        if "[" in result_text:
                            json_str = result_text[result_text.find("["):result_text.rfind("]")+1]
                            gems = json.loads(json_str)
                    except Exception as e:
                        print(f"⚠️ Hidden gems LLM error: {e}")
                
            except Exception as e:
                print(f"⚠️ [City Explorer] Hidden gems search error: {e}")
        
        return gems[:3]
