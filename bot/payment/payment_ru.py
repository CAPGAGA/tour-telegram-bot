import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from bot.utils.messages import send_message


# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def payment_menu(update: Update, context: CallbackContext):
    pass