"""
Dining Agent - Specialized agent for restaurant and food recommendations
Finds best restaurants for meals with ratings, reviews, and must-try dishes
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import httpx

SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_IMAGES_URL = "https://google.serper.dev/images"


class DiningAgent:
    """Agent specialized in finding the best restaurants and food recommendations."""
    
    name = "Dining Agent"
    description = "Finds best restaurants, local food, and dining recommendations"
    
    def __init__(self, serper_api_key: str):
        self.serper_api_key = serper_api_key
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
    
    async def find_restaurants(
        self, 
        location: str, 
        meal_type: str = "lunch",
        cuisine_preference: str = None,
        budget: str = "moderate",
        near_place: str = None,
        num_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find the best restaurants for a meal.
        
        Args:
            location: City/area name
            meal_type: "breakfast", "lunch", "dinner", "tea/snacks"
            cuisine_preference: Optional cuisine type
            budget: "budget", "moderate", "luxury"
            near_place: Optional nearby attraction
            num_results: Number of restaurants to return
        """
        print(f"🍽️ [Dining Agent] Finding {meal_type} restaurants in {location}...")
        
        restaurants = []
        
        try:
            # Build search query
            query_parts = []
            
            if near_place:
                query_parts.append(f"near {near_place}")
            
            query_parts.append(location)
            
            if meal_type == "breakfast":
                query_parts.append("best breakfast places")
            elif meal_type == "tea":
                query_parts.append("best tea shops cafes snacks")
            else:
                query_parts.append(f"best {meal_type} restaurants")
            
            if cuisine_preference:
                query_parts.append(cuisine_preference)
            
            if budget == "budget":
                query_parts.append("affordable cheap")
            elif budget == "luxury":
                query_parts.append("fine dining premium")
            
            search_query = " ".join(query_parts)
            
            # Fetch restaurants from Google Places
            places = await self._search_places(search_query, num_results + 3)
            
            for place in places[:num_results]:
                restaurant = await self._enrich_restaurant(place, location)
                if restaurant:
                    restaurants.append(restaurant)
            
            print(f"✓ [Dining Agent] Found {len(restaurants)} restaurants")
            
        except Exception as e:
            print(f"✗ [Dining Agent] Error: {e}")
        
        return restaurants
    
    async def find_meal_restaurant(
        self,
        location: str,
        meal_type: str,
        activity_before: str = None,
        activity_after: str = None,
        cuisine_preference: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a specific restaurant for a meal break in the itinerary.
        """
        print(f"🍽️ [Dining Agent] Finding {meal_type} spot in {location}...")
        
        try:
            # Build contextual query
            query_parts = [location]
            
            if meal_type == "breakfast":
                query_parts.append("best breakfast restaurant morning")
            elif meal_type == "lunch":
                query_parts.append("best lunch restaurant popular")
            elif meal_type == "dinner":
                query_parts.append("best dinner restaurant evening")
            elif meal_type in ["tea", "snacks"]:
                query_parts.append("best cafe tea shop snacks evening")
            
            if activity_before:
                query_parts.append(f"near {activity_before}")
            
            if cuisine_preference:
                query_parts.append(cuisine_preference)
            
            query_parts.append("top rated")
            
            search_query = " ".join(query_parts)
            
            places = await self._search_places(search_query, 3)
            
            if places:
                # Get the top-rated one
                return await self._enrich_restaurant(places[0], location)
            
        except Exception as e:
            print(f"✗ [Dining Agent] Error finding meal restaurant: {e}")
        
        return None
    
    async def _search_places(self, query: str, num: int) -> List[Dict]:
        """Search for restaurants using Serper Places API."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.headers,
                    json={"q": query, "num": num}
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("places", [])
            except:
                return []
    
    async def _enrich_restaurant(self, place: Dict, location: str) -> Optional[Dict[str, Any]]:
        """Enrich restaurant data with additional details."""
        name = place.get("title", "")
        if not name:
            return None
        
        restaurant = {
            "name": name,
            "cuisine": self._extract_cuisine(place),
            "rating": place.get("rating"),
            "total_reviews": place.get("ratingCount"),
            "price_level": place.get("priceLevel"),
            "address": place.get("address"),
            "phone": place.get("phoneNumber"),
            "website": place.get("website"),
            "opening_hours": place.get("openingHours"),
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "google_maps_url": None,
            "images": [],
            "must_try": [],
            "review_snippet": None,
        }
        
        # Generate Google Maps URL
        if restaurant["latitude"] and restaurant["longitude"]:
            restaurant["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={restaurant['latitude']},{restaurant['longitude']}"
        
        # Fetch images
        images = await self._fetch_images(name, location)
        restaurant["images"] = images[:3]
        
        # Fetch must-try dishes and review
        details = await self._fetch_restaurant_details(name, location)
        restaurant["must_try"] = details.get("must_try", [])
        restaurant["review_snippet"] = details.get("review_snippet")
        
        return restaurant
    
    def _extract_cuisine(self, place: Dict) -> str:
        """Extract cuisine type from place data."""
        category = place.get("category", "")
        if category:
            # Clean up category
            cuisines = ["Indian", "Chinese", "Italian", "North Indian", "South Indian", 
                       "Mughlai", "Continental", "Fast Food", "Cafe", "Multi-Cuisine"]
            for c in cuisines:
                if c.lower() in category.lower():
                    return c
            return category
        return "Multi-Cuisine"
    
    async def _fetch_images(self, name: str, location: str) -> List[str]:
        """Fetch restaurant images."""
        images = []
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(
                    SERPER_IMAGES_URL,
                    headers=self.headers,
                    json={"q": f"{name} {location} restaurant food", "num": 5}
                )
                resp.raise_for_status()
                data = resp.json()
                
                for img in data.get("images", [])[:3]:
                    url = img.get("imageUrl", "")
                    if url and "logo" not in url.lower():
                        images.append(url)
                        
            except:
                pass
        
        return images
    
    async def _fetch_restaurant_details(self, name: str, location: str) -> Dict[str, Any]:
        """Fetch must-try dishes and reviews."""
        result = {"must_try": [], "review_snippet": None}
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": f"{name} {location} must try dishes famous food menu review", "num": 5}
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("organic", [])[:3]:
                    snippet = item.get("snippet", "")
                    snippet_lower = snippet.lower()
                    
                    # Extract must-try dishes
                    if any(word in snippet_lower for word in ["must try", "famous for", "known for", "signature", "specialty", "best"]):
                        # Try to extract dish names
                        result["must_try"].append(snippet[:100])
                    
                    # Get review snippet
                    if not result["review_snippet"]:
                        if any(word in snippet_lower for word in ["delicious", "amazing", "taste", "food", "service"]):
                            result["review_snippet"] = snippet[:150]
                
                # Clean up must_try - keep only 2-3 items
                result["must_try"] = result["must_try"][:2]
                
            except:
                pass
        
        return result
