"""
Photo & Review Agent - Specialized agent for fetching real photos and review summaries
Uses Google Map Places API (Gimap) as primary + Serper as fallback
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import httpx

SERPER_IMAGES_URL = "https://google.serper.dev/images"
SERPER_PLACES_URL = "https://google.serper.dev/places"
SERPER_SEARCH_URL = "https://google.serper.dev/search"

# Gimap Google Map Places API
GOOGLE_PLACES_TEXT_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/textsearch/json"
GOOGLE_PLACES_DETAILS_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/details/json"
GOOGLE_PLACES_PHOTO_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/photo"


class PhotoReviewAgent:
    """Agent specialized in fetching real photos and reviews for places."""
    
    name = "Photo & Review Agent"
    description = "Fetches real Google photos, reviews, and map locations for places"
    
    def __init__(self, serper_api_key: str, rapidapi_key: str = None):
        self.serper_api_key = serper_api_key
        self.rapidapi_key = rapidapi_key
        self.headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json"
        }
        # Gimap API headers
        self.rapidapi_headers = {
            "x-rapidapi-host": "google-map-places.p.rapidapi.com",
            "x-rapidapi-key": rapidapi_key or ""
        }
    
    async def research_place(self, place_name: str, location: str) -> Dict[str, Any]:
        """
        Fetch comprehensive photos and reviews for a place.
        Uses: Serper (primary) → Gimap API (fallback)
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
            # 1. Try Serper first for place data (primary)
            place_data = await self._fetch_place_data_serper(place_name, location)
            if place_data:
                result["rating"] = place_data.get("rating")
                result["total_reviews"] = place_data.get("ratingCount")
                result["address"] = place_data.get("address")
                result["latitude"] = place_data.get("latitude")
                result["longitude"] = place_data.get("longitude")
                
                if result["latitude"] and result["longitude"]:
                    result["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={result['latitude']},{result['longitude']}"
            
            # 2. Fetch images from Serper (primary)
            images = await self._fetch_images_serper(place_name, location)
            result["images"] = images
            
            # 3. Fallback to Gimap if Serper didn't return data
            if not result["rating"] and self.rapidapi_key:
                gimap_data = await self._fetch_place_data_gimap(place_name, location)
                if gimap_data:
                    result["rating"] = gimap_data.get("rating")
                    result["total_reviews"] = gimap_data.get("user_ratings_total")
                    result["address"] = gimap_data.get("formatted_address", gimap_data.get("vicinity"))
                    
                    geo = gimap_data.get("geometry", {}).get("location", {})
                    result["latitude"] = geo.get("lat")
                    result["longitude"] = geo.get("lng")
                    
                    if result["latitude"] and result["longitude"]:
                        result["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={result['latitude']},{result['longitude']}"
            
            # 4. Fallback to Gimap for images if none from Serper
            if not result["images"] and self.rapidapi_key:
                gimap_data = await self._fetch_place_data_gimap(place_name, location)
                if gimap_data:
                    photos = gimap_data.get("photos", [])
                    for photo in photos[:5]:
                        photo_ref = photo.get("photo_reference")
                        if photo_ref:
                            photo_url = await self._fetch_photo_url(photo_ref)
                            if photo_url:
                                result["images"].append(photo_url)
                    print(f"✓ [Photo Review Agent] Gimap fallback: {len(result['images'])} images")
            
            # 5. Fetch review snippets and summary
            reviews = await self._fetch_reviews(place_name, location)
            result["review_snippets"] = reviews.get("snippets", [])
            result["review_summary"] = reviews.get("summary")
            
            print(f"✓ [Photo Review Agent] Found {len(result['images'])} images, rating: {result['rating']}")
            
        except Exception as e:
            print(f"✗ [Photo Review Agent] Error: {e}")
        
        return result
    
    async def _fetch_place_data_gimap(self, place_name: str, location: str) -> Optional[Dict]:
        """Fetch place details from Gimap Google Map Places API."""
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    GOOGLE_PLACES_TEXT_URL,
                    headers=self.rapidapi_headers,
                    params={
                        "query": f"{place_name} {location}",
                        "language": "en"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    return results[0] if results else None
            except Exception as e:
                print(f"⚠️ [Photo Review Agent] Gimap error: {e}")
        return None
    
    async def _fetch_photo_url(self, photo_reference: str, max_width: int = 400) -> Optional[str]:
        """Fetch actual photo URL from Gimap API by following redirects."""
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.get(
                    GOOGLE_PLACES_PHOTO_URL,
                    headers=self.rapidapi_headers,
                    params={
                        "photo_reference": photo_reference,
                        "maxwidth": str(max_width)
                    }
                )
                
                if response.status_code == 200:
                    final_url = str(response.url)
                    if "googleusercontent.com" in final_url or "ggpht.com" in final_url:
                        return final_url
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        return final_url
        except Exception as e:
            pass
        return None
    
    async def _fetch_place_data_serper(self, place_name: str, location: str) -> Optional[Dict]:
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
    
    async def _fetch_images_serper(self, place_name: str, location: str, num_images: int = 5) -> List[str]:
        """Fetch real images from Google Images via Serper (fallback)."""
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
