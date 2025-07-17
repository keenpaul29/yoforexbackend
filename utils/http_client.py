import httpx

async def fetch_json(url: str, headers: dict = None, params: dict = None):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
