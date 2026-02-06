import asyncio
import sys
import httpx
import json
sys.path.insert(0, '.')

RAPIDAPI_KEY = "1ada3e4e47msh62d3d0293eab0a8p15984cjsn11947d59282a"
SERPER_API_KEY = "2aafab11999e3ee353325f7aca6cd0d70fa673d4"

async def test_serper_places_api():
    """Test Serper Places API directly"""
    print("=" * 70)
    print("🔍 Testing Serper Places API")
    print("=" * 70)
    
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        # Test 1: Places API
        print("\n1️⃣ Testing Places API...")
        try:
            resp = await client.post(
                "https://google.serper.dev/places",
                headers=headers,
                json={"q": "Goa best lunch restaurants popular top rated", "num": 5}
            )
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                places = data.get("places", [])
                print(f"   ✅ Found {len(places)} places!")
                for p in places[:3]:
                    print(f"      - {p.get('title')} ({p.get('rating')}⭐)")
            else:
                print(f"   ❌ Error: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Search API (fallback)
        print("\n2️⃣ Testing Search API...")
        try:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers=headers,
                json={"q": "best restaurants in Goa for lunch", "num": 5}
            )
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                organic = data.get("organic", [])
                print(f"   ✅ Found {len(organic)} results!")
                for r in organic[:3]:
                    print(f"      - {r.get('title')[:50]}")
            else:
                print(f"   ❌ Error: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

async def test_dining_agent():
    """Test the dining agent"""
    from app.agents.dining_agent import DiningAgent
    
    print("\n" + "=" * 70)
    print("🍽️ Testing Dining Agent - Goa restaurants")
    print("=" * 70)
    
    agent = DiningAgent(serper_api_key=SERPER_API_KEY)
    
    # Test lunch
    print("\n1️⃣ Testing Lunch Restaurant Search...")
    lunch = await agent.find_meal_restaurant(
        location="Goa",
        meal_type="lunch"
    )
    
    if lunch:
        print(f"✅ Found: {lunch.get('name')}")
        print(f"   Cuisine: {lunch.get('cuisine')}")
        print(f"   Rating: {lunch.get('rating')}")
        print(f"   Address: {lunch.get('address')}")
    else:
        print("❌ No lunch restaurant found!")

if __name__ == '__main__':
    asyncio.run(test_serper_places_api())
    asyncio.run(test_dining_agent())
