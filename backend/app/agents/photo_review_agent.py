"""
Photo & Review Agent - Specialized agent for fetching real photos and review summaries
Uses Serper Images and Places API for real Google data
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import httpx

SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_SEARCH_URL = "https://google.serper.dev/search"


class PhotoReviewAgent:
    """Agent specialized in fetching real photos and reviews for places."""
    
    name = "Photo & Review Agent"
    description = "Fetches real Google photos, reviews, and map locations for places"
    
    def __init__(self, serper_api_key: str):
        self.serper_api_key = serper_api_key
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
    
    async def research_place(self, place_name: str, location: str) -> Dict[str, Any]:
        """
        Fetch comprehensive photos and reviews for a place.
        """
        print(f"📸 [Photo Review Agent] Fetching photos & reviews for '{place_name}'...")
        
        result = {
            "name": place_name,
            "images": [],
            "rating": None,
            "total_reviews": None,
            "review_summary": None,
            "review_snippets": [],
            "google_maps_url": None,
            "latitude": None,
            "longitude": None,
            "address": None,
        }
        
        try:
            # 1. Fetch place details (rating, reviews, location)
            place_data = await self._fetch_place_data(place_name, location)
            if place_data:
                result["rating"] = place_data.get("rating")
                result["total_reviews"] = place_data.get("ratingCount")
                result["address"] = place_data.get("address")
                result["latitude"] = place_data.get("latitude")
                result["longitude"] = place_data.get("longitude")
                
                if result["latitude"] and result["longitude"]:
                    result["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={result['latitude']},{result['longitude']}"
            
            # 2. Fetch real images
            images = await self._fetch_images(place_name, location)
            result["images"] = images
            
            # 3. Fetch review snippets and summary
            reviews = await self._fetch_reviews(place_name, location)
            result["review_snippets"] = reviews.get("snippets", [])
            result["review_summary"] = reviews.get("summary")
            
            print(f"✓ [Photo Review Agent] Found {len(result['images'])} images, rating: {result['rating']}")
            
        except Exception as e:
            print(f"✗ [Photo Review Agent] Error: {e}")
        
        return result
    
    async def _fetch_place_data(self, place_name: str, location: str) -> Optional[Dict]:
        """Fetch place details from Google Places via Serper."""
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
    
    async def _fetch_images(self, place_name: str, location: str, num_images: int = 5) -> List[str]:
        """Fetch real images from Google Images via Serper."""
        images = []
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    SERPER_IMAGES_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location} tourism", "num": num_images + 5}
                )
                resp.raise_for_status()
                data = resp.json()
                
                for img in data.get("images", []):
                    url = img.get("imageUrl", "")
                    # Filter out low-quality images
                    if url and not any(bad in url.lower() for bad in ["favicon", "logo", "icon", "placeholder"]):
                        images.append(url)
                        if len(images) >= num_images:
                            break
                
            except:
                pass
        
        return images
    
    async def _fetch_reviews(self, place_name: str, location: str) -> Dict[str, Any]:
        """Fetch review snippets and generate a summary."""
        result = {"snippets": [], "summary": None}
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                # Search for reviews
                resp = await client.post(
                    SERPER_SEARCH_URL,
                    headers=self.headers,
                    json={"q": f"{place_name} {location} reviews visitors experience", "num": 8}
                )
                resp.raise_for_status()
                data = resp.json()
                
                review_texts = []
                
                for item in data.get("organic", [])[:5]:
                    snippet = item.get("snippet", "")
                    if any(word in snippet.lower() for word in ["visit", "experience", "amazing", "beautiful", "recommend", "must", "wonderful", "review"]):
                        review_texts.append(snippet)
                        result["snippets"].append({
                            "text": snippet[:200],
                            "source": item.get("title", "")[:50]
                        })
                
                # Generate summary from collected reviews
                if review_texts:
                    combined = " ".join(review_texts[:3])
                    # Create a brief summary
                    result["summary"] = self._generate_review_summary(combined)
                
            except:
                pass
        
        return result
    
    def _generate_review_summary(self, review_text: str) -> str:
        """Generate a brief summary from review texts."""
        # Simple extraction of key sentiments
        positive_words = ["amazing", "beautiful", "wonderful", "must visit", "stunning", "peaceful", "holy", "spiritual", "great", "excellent"]
        negative_words = ["crowded", "long queue", "waiting", "expensive", "avoid"]
        
        found_positive = []
        found_negative = []
        
        text_lower = review_text.lower()
        for word in positive_words:
            if word in text_lower:
                found_positive.append(word)
        for word in negative_words:
            if word in text_lower:
                found_negative.append(word)
        
        summary_parts = []
        if found_positive:
            summary_parts.append(f"Visitors describe it as {', '.join(found_positive[:3])}")
        if found_negative:
            summary_parts.append(f"Note: Some mention {', '.join(found_negative[:2])}")
        
        return ". ".join(summary_parts) if summary_parts else "Popular tourist destination with positive reviews."
