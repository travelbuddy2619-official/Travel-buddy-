"""Test Serper API with new key"""
import httpx
import asyncio
import sys
sys.path.insert(0, '.')

SERPER_API_KEY = "1cb1689c25b1c4060f858bff8f7351d1804cbe07"

async def test_serper():
    """Test Serper API."""
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    print("Testing Serper API with new key...")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=15) as client:
        # Test places API
        r = await client.post(
            'https://google.serper.dev/places',
            headers=headers,
            json={'q': 'best restaurant in Goa', 'num': 5}
        )
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            places = data.get('places', [])
            print(f'Found {len(places)} places\n')
            for i, p in enumerate(places[:5], 1):
                print(f'{i}. {p.get("title")}')
                print(f'   Rating: {p.get("rating")} ({p.get("ratingCount")} reviews)')
                print(f'   Address: {p.get("address")}')
                print()
        else:
            print(f'Error: {r.text[:300]}')

async def test_dining_agent():
    """Test the dining agent with Serper as primary."""
    from app.agents.dining_agent import DiningAgent
    
    agent = DiningAgent(
        serper_api_key=SERPER_API_KEY,
        rapidapi_key="1ada3e4e47msh62d3d0293eab0a8p15984cjsn11947d59282a"
    )
    
    print("\n" + "=" * 50)
    print("Testing DiningAgent with Serper (primary)...")
    print("=" * 50)
    
    restaurants = await agent.find_restaurants(
        location="Goa",
        meal_type="dinner",
        num_results=3
    )
    
    print(f"\nFound {len(restaurants)} restaurants:\n")
    for i, r in enumerate(restaurants, 1):
        print(f'{i}. {r.get("name")}')
        print(f'   Rating: {r.get("rating")}')
        print(f'   Cuisine: {r.get("cuisine")}')
        print(f'   Data Source: {r.get("data_source", "N/A")}')
        images = r.get('images', [])
        if images:
            print(f'   ✅ Image: {images[0][:60]}...')
        else:
            print(f'   ❌ No image')
        print()

if __name__ == "__main__":
    asyncio.run(test_serper())
    asyncio.run(test_dining_agent())
