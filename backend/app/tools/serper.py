from __future__ import annotations

from typing import List, Optional
import httpx
from pydantic import BaseModel

from app.tools.base import BasePlanningTool


SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_PLACES_URL = "https://google.serper.dev/places"


class PlaceSearchResult(BaseModel):
    """Result from Serper place/image search."""
    name: str
    description: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    review_snippets: List[str] = []
    images: List[str] = []
    address: Optional[str] = None


class SerperInput(BaseModel):
    query: str


class SerperTool(BasePlanningTool):
    """Tool to fetch place images and info from Google via Serper API."""
    
    name = "serper_search"
    description = "Search for place images, ratings, and reviews using Google Search via Serper API."
    args_schema = SerperInput
    return_model = PlaceSearchResult

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

    async def search_images(self, query: str, num: int = 6) -> List[str]:
        """Search for images related to the query."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_IMAGES_URL,
                    headers=self.headers,
                    json={"q": query, "num": num}
                )
                resp.raise_for_status()
                data = resp.json()
                images = data.get("images", [])
                return [img.get("imageUrl") for img in images if img.get("imageUrl")][:num]
            except Exception as e:
                print(f"Serper images error: {e}")
                return []

    async def search_place(self, query: str) -> Optional[dict]:
        """Search for place details including rating and reviews."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_PLACES_URL,
                    headers=self.headers,
                    json={"q": query, "num": 1}
                )
                resp.raise_for_status()
                data = resp.json()
                places = data.get("places", [])
                if places:
                    return places[0]
                return None
            except Exception as e:
                print(f"Serper places error: {e}")
                return None

    async def get_place_info(self, place_name: str, destination: str) -> PlaceSearchResult:
        """Get comprehensive place info including images, rating, and reviews."""
        search_query = f"{place_name} {destination}"
        
        # Fetch images and place info in parallel
        images = await self.search_images(f"{search_query} tourism")
        place_data = await self.search_place(search_query)
        
        result = PlaceSearchResult(
            name=place_name,
            images=images,
        )
        
        if place_data:
            result.rating = place_data.get("rating")
            result.total_reviews = place_data.get("reviewsCount")
            result.address = place_data.get("address")
            result.description = place_data.get("description") or place_data.get("snippet")
            
            # Extract review snippets if available
            reviews = place_data.get("reviews", [])
            if reviews:
                result.review_snippets = [
                    r.get("snippet", "")[:150] for r in reviews[:3] if r.get("snippet")
                ]
        
        return result

    async def get_destination_images(self, destination: str) -> List[str]:
        """Get tourism images for a destination."""
        queries = [
            f"{destination} tourist attractions",
            f"{destination} famous places",
            f"{destination} travel photography",
        ]
        
        all_images = []
        for query in queries[:1]:  # Limit to save API calls
            images = await self.search_images(query, num=4)
            all_images.extend(images)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in all_images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images[:6]

    async def _arun(self, **kwargs) -> PlaceSearchResult:
        """Run a general place search."""
        query = kwargs["query"]
        return await self.get_place_info(query, "")
