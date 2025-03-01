import os
import aiohttp

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.payment.utils import fetch_tour_payment_details

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def render_payment_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    tour_id = int(query.data.split("_")[-1])

    invoice_data = await fetch_tour_payment_details(tour_id, 'paypal')

    if not  invoice_data:
        keyboard = [[InlineKeyboardButton('🛒 Back to tour page', callback_data=f"view_tour_{tour_id}")]]
        await query.message.edit_text(
            "❌ Failed to generate payment details. Try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
