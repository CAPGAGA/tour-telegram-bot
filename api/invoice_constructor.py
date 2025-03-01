import os
import logging

from datetime import datetime

import aiohttp
from fastapi import HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Rout, BaseUser
from api.handlers import create_payment_token
from api.settings import PAYPAL_API_URL, PAYPAL_SECRET, PAYPAL_CLIENT_ID

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

class InvoiceConstructor:

    @staticmethod
    async def _fetch_tour_details(tour_id: int, session: AsyncSession):
        """
        Fetch tour details from the database
        """
        result = await session.execute(select(Rout).where(Rout.id == tour_id))
        tour = result.scalars().first()
        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")
        return tour

    @staticmethod
    async def _fetch_user_details(user_id: int, session: AsyncSession):
        """
        Fetch user details from the database
        """
        result = await session.execute(select(BaseUser).where(BaseUser.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def return_invoice_paypal_link(
            tour_id: int,
            user_id: int,
            session: AsyncSession
    ) -> dict:
        """
        Construct an invoice for PayPal payments
        """
        # Get data from db

        tour_data = await InvoiceConstructor._fetch_tour_details(tour_id, session)
        user_data = await InvoiceConstructor._fetch_user_details(user_id, session)

        if not tour_data or not user_data:
            raise HTTPException(status_code=500, detail="Invoice generation failed")

        invoice_id = f"ORD-{tour_id}-{user_id}-{int(datetime.utcnow().timestamp())}"

        async with aiohttp.ClientSession() as client_session:

            # Get PayPal Access Token
            auth = aiohttp.BasicAuth(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
            async with client_session.post(
                    f"{PAYPAL_API_URL}/v1/oauth2/token",
                    auth=auth,
                    data={"grant_type": "client_credentials"}
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail='Failed to authenticate with PayPal')
                token_data = await response.json()
                access_token = token_data["access_token"]
            order_sign = create_payment_token(user_id, tour_id, invoice_id)
            # Create PayPal Order
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": invoice_id,
                        "amount": {
                            "currency_code": "USD",
                            "value": str(tour_data.base_price)
                        },
                        "description": f'Access to tour: "{tour_data.rout_name}"'
                    }
                ],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "return_url": f"{API_BASE_URL}/order/complete/paypal/success/{order_sign}",
                            "cancel_url": f"{API_BASE_URL}/order/complete/paypal/cancel/{order_sign}",
                            "brand_name": "PocketTour",
                            "landing_page": "GUEST_CHECKOUT",
                            "user_action": "PAY_NOW",
                            "shipping_preference": "NO_SHIPPING",
                            "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                            "locale": "en-US"
                        }
                    }
                }
            }

            async with client_session.post(
                    f"{PAYPAL_API_URL}/v2/checkout/orders",
                    headers=headers,
                    json=payload
            ) as response:
                if response.status not in (200, 201):
                    raise HTTPException(status_code=500, detail="Failed to create PayPal order")

                order_data = await response.json()
                logger.info(order_data)
                approval_link = next(
                    (link["href"] for link in order_data["links"] if link["rel"] == "payer-action"), None)
                logger.info(approval_link)
                if not approval_link:
                    raise HTTPException(status_code=500, detail="Failed to generate PayPal link")

                return {
                    "invoice_id": invoice_id,
                    "approval_link": approval_link,
                    "amount": tour_data.base_price,
                    "payment_method": "paypal"
                }
