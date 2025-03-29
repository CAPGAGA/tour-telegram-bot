import os

import aiohttp

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def set_language(
        user_id: int,
        lang: str
):
    """
    Saves language into database
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                    f"{API_BASE_URL}/user/set-language-external",
                    params={"user_id": user_id, "lang": lang}
            ) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None
