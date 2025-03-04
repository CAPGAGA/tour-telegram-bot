import aiohttp
import os
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")


def user_auth(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        telegram_id = update.effective_user.id
        username = update.effective_user.username or f"user_{telegram_id}"  # Fallback if no username

        # Payload for user registration
        payload = {
            "user_id": telegram_id,
            "username": username,
            "is_admin": False  # Default to non-admin
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{API_BASE_URL}/auth/register-telegram", json=payload) as response:
                    if response.status != 200:
                        await update.message.reply_text("❌ Error while registering. Please try again later.")
                        return

                    user = await response.json()  # Convert response to JSON

            except aiohttp.ClientError as e:
                await update.message.reply_text("❌ Network error. Please try again later.")
                return

        # Pass user data to the handler
        return await func(update, context, user, *args, **kwargs)

    return wrapper