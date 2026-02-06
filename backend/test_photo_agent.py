"""Test Photo Review Agent with Serper as primary"""
import asyncio
import sys
sys.path.insert(0, '.')

SERPER_API_KEY = "1cb1689c25b1c4060f858bff8f7351d1804cbe07"
RAPIDAPI_KEY = "1ada3e4e47msh62d3d0293eab0a8p15984cjsn11947d59282a"

async def test():
    from app.agents.photo_review_agent import PhotoReviewAgent
    
    agent = PhotoReviewAgent(
        serper_api_key=SERPER_API_KEY,
        rapidapi_key=RAPIDAPI_KEY
    )
    
    print("Testing PhotoReviewAgent with Serper (primary)...")
    print("=" * 50)
    
    result = await agent.research_place('Baga Beach', 'Goa')
    
    print(f"Place: {result['name']}")
    print(f"Rating: {result['rating']}")
    print(f"Reviews: {result['total_reviews']}")
    print(f"Address: {result['address']}")
    print(f"Images: {len(result['images'])}")
    
    if result['images']:
        for i, img in enumerate(result['images'][:3], 1):
            print(f"  {i}. {img[:70]}...")
    else:
        print("  No images found")

if __name__ == "__main__":
    asyncio.run(test())
