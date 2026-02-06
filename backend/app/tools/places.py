from __future__ import annotations

from typing import List, Optional, Dict, Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from app.models import PlaceDetails, ReviewSummary, PopularTimeSlot, Restaurant
from app.tools.base import BasePlanningTool

MAPTILER_GEOCODING_URL = "https://api.maptiler.com/geocoding/{query}.json"
SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_SEARCH_URL = "https://google.serper.dev/search"


class PlaceDetailsInput(BaseModel):
    location: str


class PlaceDetailsTool(BasePlanningTool):
    name = "get_place_details"
    description = (
        "Looks up destination highlights via MapTiler and Serper APIs. "
        "Returns structured location insights including real Google images, "
        "ratings, reviews, and estimated popular times."
    )
    args_schema = PlaceDetailsInput
    return_model = PlaceDetails

    def __init__(self, api_key: str, serper_api_key: Optional[str] = None):
        self.api_key = api_key
        self.serper_api_key = serper_api_key
        self.serper_headers = {
            "X-API-KEY": serper_api_key or "",
            "Content-Type": "application/json"
        }

    async def _fetch_serper_images(self, query: str, num: int = 4) -> List[str]:
        """Fetch real images from Google Images via Serper."""
        if not self.serper_api_key:
            return []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_IMAGES_URL,
                    headers=self.serper_headers,
                    json={"q": query, "num": num + 2}  # Fetch extra for filtering
                )
                resp.raise_for_status()
                data = resp.json()
                images = data.get("images", [])
                
                # Filter for good quality images (prefer larger ones)
                valid_images = []
                for img in images:
                    url = img.get("imageUrl", "")
                    # Skip very small thumbnails and invalid URLs
                    if url and not any(x in url.lower() for x in ["favicon", "logo", "icon", "1x1", "pixel"]):
                        valid_images.append(url)
                    if len(valid_images) >= num:
                        break
                
                return valid_images[:num]
            except Exception as e:
                print(f"Serper images error: {e}")
                return []

    async def _fetch_serper_place(self, query: str) -> Optional[dict]:
        """Fetch place details from Google via Serper."""
        if not self.serper_api_key:
            return None
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.serper_headers,
                    json={"q": query, "num": 1}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                return places[0] if places else None
            except Exception as e:
                print(f"Serper places error: {e}")
                return None

    async def fetch_restaurants(self, location: str, num: int = 6) -> List[Restaurant]:
        """Fetch real restaurants from Google via Serper Places API."""
        if not self.serper_api_key:
            return []
        
        restaurants = []
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Search for restaurants in the location
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.serper_headers,
                    json={"q": f"best restaurants in {location}", "num": num}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                
                for place in places[:num]:
                    # Extract review snippet if available
                    review_snippet = None
                    if place.get("reviews"):
                        first_review = place["reviews"][0] if place["reviews"] else {}
                        review_snippet = first_review.get("snippet", "")
                        if review_snippet and len(review_snippet) > 120:
                            review_snippet = review_snippet[:120] + "..."
                    
                    # Determine cuisine from category or title
                    cuisine = place.get("category", "")
                    if not cuisine and place.get("type"):
                        cuisine = place["type"]
                    
                    # Map price level
                    price_raw = place.get("priceLevel", "")
                    price_level = price_raw if price_raw else "$$"
                    
                    restaurant = Restaurant(
                        name=place.get("title", "Unknown Restaurant"),
                        cuisine=cuisine if cuisine else "Local Cuisine",
                        rating=place.get("rating"),
                        total_reviews=place.get("reviewsCount"),
                        price_level=price_level,
                        address=place.get("address"),
                        phone=place.get("phoneNumber"),
                        website=place.get("website"),
                        review_snippet=review_snippet
                    )
                    restaurants.append(restaurant)
                    
            except Exception as e:
                print(f"Serper restaurants error: {e}")
        
        return restaurants

    async def fetch_restaurant_details(self, restaurant_name: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed info about a specific restaurant including images and reviews."""
        if not self.serper_api_key:
            return None
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Search for the specific restaurant
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.serper_headers,
                    json={"q": f"{restaurant_name} restaurant {location}", "num": 3}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                
                if not places:
                    return None
                
                # Find best matching restaurant
                place = places[0]
                for p in places:
                    if restaurant_name.lower() in p.get("title", "").lower():
                        place = p
                        break
                
                # Fetch images for this restaurant
                images = await self._fetch_serper_images(f"{restaurant_name} {location} restaurant food", num=3)
                
                # Extract review snippets
                review_snippets = []
                for review in place.get("reviews", [])[:3]:
                    snippet = review.get("snippet", "")
                    if snippet:
                        clean_snippet = snippet.strip()
                        if len(clean_snippet) > 100:
                            clean_snippet = clean_snippet[:100] + "..."
                        review_snippets.append(clean_snippet)
                
                review_summary = " | ".join(review_snippets[:2]) if review_snippets else None
                
                # Get cuisine from category
                cuisine = place.get("category", "")
                if not cuisine:
                    cuisine = place.get("type", "Restaurant")
                
                return {
                    "name": place.get("title", restaurant_name),
                    "cuisine": cuisine,
                    "rating": place.get("rating"),
                    "totalReviews": place.get("reviewsCount"),
                    "priceLevel": place.get("priceLevel", "$$"),
                    "address": place.get("address"),
                    "phone": place.get("phoneNumber"),
                    "website": place.get("website"),
                    "reviewSnippet": review_summary,
                    "images": images,
                    "openingHours": place.get("openingHours"),
                }
                
            except Exception as e:
                print(f"Serper restaurant details error for {restaurant_name}: {e}")
                return None

    async def fetch_attraction_details(self, attraction_name: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch real details for a specific attraction from Google via Serper."""
        if not self.serper_api_key:
            return None
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Search for the specific attraction
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.serper_headers,
                    json={"q": f"{attraction_name} {location} tourist attraction", "num": 3}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                
                if not places:
                    # Try a simpler search
                    resp = await client.post(
                        SERPER_PLACES_URL,
                        headers=self.serper_headers,
                        json={"q": f"{attraction_name} {location}", "num": 3}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    places = data.get("places", [])
                
                if not places:
                    return None
                
                # Find best matching place
                place = places[0]
                for p in places:
                    if attraction_name.lower() in p.get("title", "").lower():
                        place = p
                        break
                
                # Get real images for this attraction from Google Images
                images = await self._fetch_serper_images(f"{attraction_name} {location}", num=4)
                
                # Extract multiple review snippets and combine them
                review_snippets = []
                for review in place.get("reviews", [])[:3]:
                    snippet = review.get("snippet", "")
                    if snippet:
                        # Clean up and truncate
                        clean_snippet = snippet.strip()
                        if len(clean_snippet) > 80:
                            clean_snippet = clean_snippet[:80] + "..."
                        review_snippets.append(clean_snippet)
                
                # Create a combined review summary
                review_summary = None
                if review_snippets:
                    review_summary = " | ".join(review_snippets[:2])  # Combine first 2 reviews
                
                return {
                    "name": place.get("title", attraction_name),
                    "rating": place.get("rating"),
                    "totalReviews": place.get("reviewsCount"),
                    "reviewSummary": review_summary,
                    "address": place.get("address"),
                    "images": images if images else [],
                    "category": place.get("category", ""),
                    "website": place.get("website"),
                    "phone": place.get("phoneNumber"),
                    "openingHours": place.get("openingHours"),
                }
                
            except Exception as e:
                print(f"Serper attraction error for {attraction_name}: {e}")
                return None

    async def fetch_practical_info(self, place_name: str, location: str) -> Optional[Dict[str, Any]]:
        """
        Fetch practical/realistic information about a place using Google Search.
        This includes typical visit duration, best time to visit, ticket info, tips, etc.
        """
        if not self.serper_api_key:
            return None
        
        async with httpx.AsyncClient(timeout=20) as client:
            practical_info = {
                "typicalDuration": None,
                "bestTimeToVisit": None,
                "ticketInfo": None,
                "openingHours": None,
                "importantTips": [],
                "warnings": [],
            }
            
            try:
                # Search for visit duration and timing info
                search_query = f"{place_name} {location} how long does it take visit duration hours"
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.serper_headers,
                    json={"q": search_query, "num": 5}
                )
                resp.raise_for_status()
                data = resp.json()
                
                # Extract from answer box if available
                if data.get("answerBox"):
                    answer = data["answerBox"]
                    snippet = answer.get("snippet") or answer.get("answer", "")
                    if snippet:
                        practical_info["typicalDuration"] = snippet[:200]
                
                # Extract from knowledge graph
                if data.get("knowledgeGraph"):
                    kg = data["knowledgeGraph"]
                    if kg.get("attributes"):
                        attrs = kg["attributes"]
                        if "Hours" in attrs:
                            practical_info["openingHours"] = attrs["Hours"]
                        if "Duration" in attrs:
                            practical_info["typicalDuration"] = attrs["Duration"]
                
                # Extract from organic results
                organic = data.get("organic", [])
                for result in organic[:3]:
                    snippet = result.get("snippet", "").lower()
                    title = result.get("title", "").lower()
                    full_snippet = result.get("snippet", "")
                    
                    # Look for duration info
                    if any(word in snippet for word in ["hours", "hour", "minutes", "duration", "takes", "spend"]):
                        if not practical_info["typicalDuration"]:
                            practical_info["typicalDuration"] = full_snippet[:200]
                    
                    # Look for timing/tips
                    if any(word in snippet for word in ["best time", "recommend", "tip", "avoid", "crowd"]):
                        practical_info["importantTips"].append(full_snippet[:150])
                
                # Second search for ticket and practical tips
                search_query2 = f"{place_name} {location} ticket booking timings tips visitors guide"
                resp2 = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.serper_headers,
                    json={"q": search_query2, "num": 5}
                )
                resp2.raise_for_status()
                data2 = resp2.json()
                
                organic2 = data2.get("organic", [])
                for result in organic2[:3]:
                    snippet = result.get("snippet", "").lower()
                    full_snippet = result.get("snippet", "")
                    
                    # Look for ticket info
                    if any(word in snippet for word in ["ticket", "entry fee", "booking", "free entry", "rs", "₹", "inr"]):
                        if not practical_info["ticketInfo"]:
                            practical_info["ticketInfo"] = full_snippet[:200]
                    
                    # Look for timing info
                    if any(word in snippet for word in ["open", "close", "timing", "am", "pm"]):
                        if not practical_info["openingHours"]:
                            practical_info["openingHours"] = full_snippet[:150]
                    
                    # Look for warnings/important info
                    if any(word in snippet for word in ["warning", "note", "important", "must", "required", "queue", "waiting"]):
                        practical_info["warnings"].append(full_snippet[:150])
                
                # Limit tips and warnings
                practical_info["importantTips"] = practical_info["importantTips"][:3]
                practical_info["warnings"] = practical_info["warnings"][:2]
                
                return practical_info
                
            except Exception as e:
                print(f"Serper practical info error for {place_name}: {e}")
                return None

    async def _arun(self, **kwargs) -> PlaceDetails:
        location = kwargs["location"]
        
        # Fetch MapTiler geocoding data
        async with httpx.AsyncClient(timeout=20) as client:
            query = quote(location)
            url = MAPTILER_GEOCODING_URL.format(query=query)
            params = {"key": self.api_key, "language": "en", "limit": 1}
            search_resp = await client.get(url, params=params)
            search_resp.raise_for_status()
            data = search_resp.json()
            features = data.get("features", [])
            if not features:
                raise ValueError(f"No MapTiler data found for {location}")
            feature = features[0]
            properties = feature.get("properties", {})

        # Fetch Serper data (images and place info)
        photos = await self._fetch_serper_images(location)
        serper_place = await self._fetch_serper_place(f"{location} tourist destination")
        
        # Build review summary from Serper or fallback
        if serper_place:
            rating = serper_place.get("rating", 4.5)
            total_reviews = serper_place.get("reviewsCount", 1000)
            highlights = []
            
            # Extract review snippets
            reviews = serper_place.get("reviews", [])
            for review in reviews[:3]:
                snippet = review.get("snippet", "")
                if snippet:
                    highlights.append(snippet[:100] + "..." if len(snippet) > 100 else snippet)
            
            if not highlights:
                highlights = self._build_highlights(properties, location)
            
            review_summary = ReviewSummary(
                rating=rating,
                total_reviews=total_reviews,
                highlights=highlights,
            )
        else:
            review_summary = ReviewSummary(
                rating=4.5,
                total_reviews=1000,
                highlights=self._build_highlights(properties, location),
            )
        
        summary = self._build_summary(properties, location)
        popular_times = self._estimate_popular_times(properties)

        return PlaceDetails(
            location=properties.get("name", location),
            summary=summary,
            photos=photos if photos else self._fallback_photos(location),
            reviews=review_summary,
            popular_times=popular_times,
        )

    def _fallback_photos(self, location: str) -> List[str]:
        """Fallback to Unsplash if Serper fails."""
        encoded = quote(location)
        return [
            f"https://source.unsplash.com/800x600/?{encoded},travel",
            f"https://source.unsplash.com/800x600/?{encoded},tourism",
            f"https://source.unsplash.com/800x600/?{encoded},landscape",
            f"https://source.unsplash.com/800x600/?{encoded},architecture",
        ]

    def _build_summary(self, props: dict, fallback: str) -> str:
        categories = props.get("categories") or []
        region = props.get("region") or props.get("country")
        category_text = ", ".join(categories[:2]) if categories else "notable sights"
        return f"{props.get('name', fallback)} sits within {region or 'this region'} and is known for {category_text}."

    def _build_highlights(self, props: dict, fallback: str) -> List[str]:
        highlights: List[str] = []
        if props.get("categories"):
            highlights.append(
                f"Travelers mention {', '.join(props['categories'][:3])} as signature experiences."
            )
        if props.get("population"):
            highlights.append(
                f"Local population of roughly {props['population']:,} keeps the area lively without feeling overwhelming."
            )
        if not highlights:
            highlights.append(f"{props.get('name', fallback)} delivers authentic local character and easy navigation.")
        return highlights

    def _estimate_popular_times(self, props: dict) -> List[PopularTimeSlot]:
        layer = props.get("layer") or "destination"
        if layer in {"poi", "landmark"}:
            return [
                PopularTimeSlot(day="Weekdays", busyness_text="Steady foot traffic from late morning to early evening."),
                PopularTimeSlot(day="Weekends", busyness_text="Expect peak visits midday with sunset crowds."),
            ]
        return [
            PopularTimeSlot(day="Typical", busyness_text="Most visitors arrive mid-afternoon for relaxed exploration."),
        ]
