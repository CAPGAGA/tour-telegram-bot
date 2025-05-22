import os
import aiohttp

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")


async def fetch_tour_payment_details(
        user_id: int,
        tour_id: int,
        method: str,
        subject: str,
        discount: str,
        promo_type: str
):
    """
        Fetch necessary data to insert into payment button
        tour_id: int - internal id of tour for which payment is being made
        method: str - name of payment gateway to fetch info for e.g 'telegram', 'paypal' etc
    """
    async with aiohttp.ClientSession() as session:
        try:
            data = {
                "user_id": user_id,
                "rout_id": tour_id,
                "discount_value": discount,
                "discount_type": promo_type
            }
            async with session.post(f"{API_BASE_URL}/order/create/{method}", json=data) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None

async def complete_order(
        method: str,
        token: str
) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/order/complete/{method}/success/{token}") as response:
                if response.status != 200:
                    return False
                return True
        except aiohttp.ClientError:
            return False

async def get_gift_code(
        invoice_id: str
):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/promo/create-gift", json={"invoice_id": invoice_id}) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None