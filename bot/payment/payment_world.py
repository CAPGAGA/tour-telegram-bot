import os
import aiohttp
import logging

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from bot.payment.utils import fetch_tour_payment_details

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")
logger = logging.getLogger(__name__)

@user_auth
async def render_paypal_payment_menu(
        update: Update,
        context: CallbackContext,
        user: dict
):
    """Handle PayPal payments with or without promo codes"""
    _ = context._  # For translations if available
    query = update.callback_query
    await query.answer()

    callback_parts = query.data.split("_")
    tour_id = int(callback_parts[-1])
    method = callback_parts[-2]
    subject = callback_parts[-3]
    discount = callback_parts[-4]
    promo_type = callback_parts[-5]
    user_id = user.get('id')

    invoice_data = await fetch_tour_payment_details(
        tour_id=tour_id,
        user_id=user_id,
        method=method,
        subject=subject,
        discount=discount,
        promo_type=promo_type
    )

    if not invoice_data:
        keyboard = [[InlineKeyboardButton('🛒 Back to tour page', callback_data=f"view_tour_None_None_{tour_id}")]]
        await query.message.edit_text(
            "❌ Failed to generate payment details. Try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = [
        [InlineKeyboardButton('Proceed to payment page', web_app=WebAppInfo(url=invoice_data['payment_link']))],
        [InlineKeyboardButton('🔙 Back to tour page', callback_data=f"view_tour_None_None_{tour_id}")]
    ]

    await query.message.edit_text(
        "Your payment link is ready! Click button below and follow instructions to complete your order!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )