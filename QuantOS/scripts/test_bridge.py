import httpx
import asyncio

async def test_bridge():
    url = "http://127.0.0.1:8001/api/status"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            print(f"Bridge Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
        except Exception as e:
            print(f"Bridge Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_bridge())
