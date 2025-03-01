import aiohttp
import os

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def fetch_tour_details(tour_id):
    """Fetch individual tour details from API."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/rout/get-rout/detailed/{tour_id}") as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None

async def show_tour_details(update: Update, context: CallbackContext):
    """Display details of a selected tour."""
    query = update.callback_query
    await query.answer()

    tour_id = query.data.split("_")[-1]
    tour = await fetch_tour_details(tour_id)

    if not tour:
        keyboard = [[InlineKeyboardButton('🛒 Back to shop', callback_data="buy_tours")]]
        await query.message.edit_text(
            "❌ Failed to load tour details. Try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    rout_name = escape_markdown(tour["rout_name"], version=2)
    base_price = escape_markdown(str(tour["base_price"]), version=2)
    description = escape_markdown(tour["rout_description"], version=2)
    distance = escape_markdown(str(round(float(tour['distance']), 2)), version=2)
    points = escape_markdown(str(tour['total_points']), version=2)

    # Tour description (trim if too long)
    if len(description) > 600:
        description = description[:600] + "..."

    # Create tour card message
    tour_text = (f"🗺 **{rout_name}**"
                 f"\n\n💵 **Price:** {base_price}$"
                 f"\n\n📖 **Description:** {description} "
                 f"\n\n📢 **Points:** {points} ┃ 📏 **Distance:** {distance} km  ")

    # Create purchase buttons
    keyboard = [
        [InlineKeyboardButton("🛍 Buy for Me", callback_data=f"buy_me_{tour_id}")],
        [InlineKeyboardButton("🎁 Buy for Friend", callback_data=f"buy_friend_{tour_id}")],
        [InlineKeyboardButton("💵 I have promo code", callback_data=f"buy_promo_{tour_id}")],
        [InlineKeyboardButton("🔙 Back to Tour List", callback_data="buy_tours")]
    ]

    await query.message.edit_text(
        tour_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
    )
