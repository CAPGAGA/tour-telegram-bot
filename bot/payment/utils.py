import os
import aiohttp

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def fetch_tour_payment_details(
        tour_id: int,
        method: str
):
    """
        Fetch necessary data to create payment invoice for client
        tour_id: int - internal id of tour for which payment is being made
        method: str - name of payment gateway to fetch info for e.g 'telegram', 'paypal' etc
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/rout/get-rout/invoice-details/{tour_id}/{method}") as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None