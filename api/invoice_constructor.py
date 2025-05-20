import os
import logging

from datetime import datetime
from typing import Optional

import aiohttp
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import LabeledPrice

from db.database import get_session
from db.models import Rout, BaseUser, CurrencyRates
from api.handlers import create_payment_token
from settings import PAYPAL_API_URL, PAYPAL_SECRET, PAYPAL_CLIENT_ID, TELEGRAM_PAYMENT_PROVIDER, TELEGRAM_CURRENCY

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

class InvoiceConstructor:

    @staticmethod
    async def _convert_currency(
            amount_usd: float,
            target_currency: str
    ) -> float:
        """
        Converts price to other currency
        """
        target_currency = target_currency.upper()
        if target_currency not in ["USD", "EUR", "RUB"]:
            raise ValueError(f"Unsupported currency: {target_currency}")

        async for session in get_session():
            async with session.begin():
                result = await session.execute(
                    select(CurrencyRates)
                    .order_by(CurrencyRates.created_at.desc()).limit(1)
                )
                rates: CurrencyRates = result.scalar_one_or_none()

                if not rates:
                    raise Exception("Currency rates not found")

                if target_currency == "USD":
                    return amount_usd * float(rates.usd_usd)
                elif target_currency == "EUR":
                    return amount_usd * float(rates.usd_eur)
                elif target_currency == "RUB":
                    return amount_usd * float(rates.usd_rub)
                return None
        return None

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
            discount_type: str,
            discount_value: str,
            session: AsyncSession,
    ) -> dict:
        """
        Construct an invoice for PayPal payments
        """
        # Get data from db
        tour_data = await InvoiceConstructor._fetch_tour_details(tour_id, session)
        user_data = await InvoiceConstructor._fetch_user_details(user_id, session)

        if not tour_data or not user_data:
            raise HTTPException(status_code=500, detail="Invoice generation failed")

        base_price = tour_data.base_price
        final_price = base_price
        price_description = f'Access to tour: "{tour_data.rout_name}"'

        # Apply discount if provided
        if discount_type != 'None':
            try:
                discount_value_float = float(discount_value)
                if discount_type == "flat":
                    final_price = max(0, base_price - discount_value_float)
                    price_description = f'Access to tour: "{tour_data.rout_name}" (${base_price:.2f} - ${discount_value_float:.2f} discount)'
                elif discount_type == "percent":
                    discount_amount = (base_price * discount_value_float) / 100
                    final_price = max(0, base_price - discount_amount)
                    price_description = f'Access to tour: "{tour_data.rout_name}" (${base_price:.2f} - {discount_value_float}% off)'
            except ValueError:
                logger.error(f"Invalid discount value: {discount_value}")
                # Continue with base price if discount calculation fails
                final_price = base_price

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
                            "value": str(final_price)
                        },
                        "description": price_description
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
                    (
                        link["href"] for link in order_data["links"] if link["rel"] == "payer-action"
                    ),
                    None
                )

                if not approval_link:
                    raise HTTPException(status_code=500, detail="Failed to generate PayPal link")

                return {
                    "invoice_id": invoice_id,
                    "approval_link": approval_link,
                    "amount": final_price,
                    "payment_method": "paypal"
                }

    @staticmethod
    async def return_invoice_telegram_json(
            user_id: int,
            tour_id: int,
            discount_type: Optional[str],
            discount_value: Optional[str],
            session: AsyncSession
    ) -> dict:
        """
        Construct an invoice for Telegram payments
        """

        # Get data from db
        tour_data = await InvoiceConstructor._fetch_tour_details(tour_id, session)
        user_data = await InvoiceConstructor._fetch_user_details(user_id, session)

        if not tour_data or not user_data:
            raise HTTPException(status_code=500, detail="Invoice generation failed")

        invoice_id = f"YK-ORD-{tour_id}-{user_id}-{int(datetime.utcnow().timestamp())}"

        base_price = await InvoiceConstructor._convert_currency(tour_data.base_price, TELEGRAM_CURRENCY)
        final_price = base_price
        price_label = tour_data.rout_name

        if discount_type != 'None':
            try:
                discount_value_float = float(discount_value)
                if discount_type == "flat":
                    final_price = max(0, base_price - discount_value_float)
                    price_label = f"{tour_data.rout_name} (${base_price:.2f} - ${discount_value_float:.2f} discount)"
                elif discount_type == "percent":
                    discount_amount = (base_price * discount_value_float) / 100
                    final_price = max(0, base_price - discount_amount)
                    price_label = f"{tour_data.rout_name} (${base_price:.2f} - {discount_value_float}% off)"
            except ValueError:
                logger.error(f"Invalid discount value: {discount_value}")
                # Continue with base price if discount calculation fails
                final_price = base_price

        invoice_payload = {
            "title": f"{tour_data.rout_name} Tour",
            "description": tour_data.rout_description[:200],  # Telegram limits description length
            "payload": invoice_id,  # Unique identifier for tracking payments
            "provider_token": TELEGRAM_PAYMENT_PROVIDER,
            "currency": TELEGRAM_CURRENCY,
            "prices": {
                'label': price_label,
                'price': str(final_price),
            },
            "start_parameter": f"buy_tour_{tour_id}",
            "need_email": True,
            "need_phone_number": False,
            "send_email_to_provider": True,
            "send_phone_number_to_provider": False,
            "is_flexible": False,
            "protect_content": True,

        }

        order_sign = create_payment_token(user_id, tour_id, invoice_id)

        return {
            "invoice_id": invoice_id,
            "invoice_payload": invoice_payload,
            "order_sign": order_sign,
            "amount": final_price,
            "payment_method": "yookassa"
        }

