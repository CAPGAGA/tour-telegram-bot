import logging
import aiohttp

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from db.database import get_session
from db.models import CurrencyRates
from settings import CURRENCY_CONVERTER_API_KEY

logger = logging.getLogger(__name__)

CURRENCY_API_URL = f"https://api.freecurrencyapi.com/v1/latest?apikey={CURRENCY_CONVERTER_API_KEY}&currencies=EUR%2CUSD%2CRUB"

async def fetch_and_store_currency_rates():
    async with aiohttp.ClientSession() as http_session:
        async with http_session.get(CURRENCY_API_URL) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch rates: {response.status}")
            data = await response.json()

    rates = data.get("data")
    if not rates:
        raise Exception("No data in currency response")

    usd_usd = float(rates.get("USD", 1))
    usd_eur = float(rates.get("EUR", 0))
    usd_rub = float(rates.get("RUB", 0))

    # Insert into database
    stmt = insert(CurrencyRates).values(
        usd_usd=usd_usd,
        usd_eur=usd_eur,
        usd_rub=usd_rub,
        created_at=datetime.utcnow()
    )
    async for session in get_session():
        async with session.begin():
            await session.execute(stmt)
            await session.commit()

    logger.info("💸 Currency rates updated successfully")

async def ensure_currency_rates():
    """Checks if currency rates exist; if not, fetches and inserts them."""
    async for session in get_session():
        async with session.begin():
            result = await session.execute(select(CurrencyRates).order_by(CurrencyRates.created_at.desc()).limit(1))
            existing_rate = result.scalar_one_or_none()

            if existing_rate:
                logger.info("✅ Currency rates already exist in the database.")
                return  # No need to fetch new rates

    logger.warning("⚠️ No rates found! Fetching new currency rates...")
    await fetch_and_store_currency_rates()