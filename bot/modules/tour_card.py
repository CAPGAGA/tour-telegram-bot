import aiohttp
import os

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from bot.decorators.auth import user_auth

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

async def fetch_users_tours(user_id):
    """Fetch tours owned by user"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                    f"{API_BASE_URL}/user_routs/get-user-rout", params={"user_id": user_id}
            ) as response:
                if response.status != 200:
                    return []
                return await response.json()
        except aiohttp.ClientError:
            return []


@user_auth
async def show_tour_details(
        update: Update,
        context: CallbackContext,
        user
):
    """Display details of a selected tour."""
    _ = context._

    query = update.callback_query
    await query.answer()

    tour_id = query.data.split("_")[-1]
    promo_discount = query.data.split("_")[-2]
    promo_type = query.data.split("_")[-3]

    tour = await fetch_tour_details(tour_id)
    user_tours = await fetch_users_tours(user.get("id"))
    is_owned = False

    if user_tours:
        for user_tour in user_tours:
            if user_tour['rout_id'] == int(tour_id):
                is_owned = True

    if not tour:
        keyboard = [[InlineKeyboardButton("🛒 " + _("Back to shop"), callback_data="buy_tours")]]
        await query.message.edit_text(
            "❌ " + _("Failed to load tour details. Try again later."),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    rout_name_raw = tour["rout_name"]
    base_price_raw = str(tour["base_price"])
    description_raw = tour["rout_description"]
    distance_raw = str(round(float(tour['distance']), 2))
    points_raw = str(tour['total_points'])

    rout_name = escape_markdown(rout_name_raw, version=2)
    base_price = escape_markdown(base_price_raw, version=2)
    description = escape_markdown(description_raw, version=2)
    distance = escape_markdown(distance_raw, version=2)
    points = escape_markdown(points_raw, version=2)

    # After the base price section and before creating tour_text

    # Calculate price with promo if applicable
    final_price = base_price_raw
    if promo_type != 'None' and promo_discount != 'None':
        if promo_type == "flat":
            final_price = max(0, float(base_price_raw) - float(promo_discount))
        elif promo_type == "percent":
            discount_amount = (float(base_price_raw) * float(promo_discount)) / 100
            final_price = max(0, float(base_price_raw) - discount_amount)
        
        final_price = str(round(final_price, 2))
        final_price = escape_markdown(final_price, version=2)

        # Update tour text to include both prices
        tour_text = (f"🗺 **{rout_name}**"
                     f"\n💰 **" + _("Your Price") + f":** {final_price}$"
                     f"\n\n📖 **" + _("Description") + f":** {description} "
                     f"\n\n📢 **" + _("Points") + f":** {points} ┃ 📏 **" + _("Distance" ) + f":** {distance} km  ")
    else:
        # Original tour text without promo
        tour_text = (f"🗺 **{rout_name}**"
                     f"\n\n💵 **" + _("Price") + f":** {base_price}$"
                     f"\n\n📖 **" + _("Description") + f":** {description} "
                     f"\n\n📢 **" + _("Points") + f":** {points} ┃ 📏 **" + _("Distance" ) + f":** {distance} km  ")

    # Tour description (trim if too long)
    if len(description) > 600:
        description = description[:600] + "..."

    if float(final_price) == 0:
        # Create add to my account keyboard
        keyboard = [
            [InlineKeyboardButton("➕ " + _("Add to My Account"), callback_data=f"add_tour_{tour_id}")],
            [InlineKeyboardButton("🔙 " + _("Back to Tour List"), callback_data="buy_tours")]
        ]
    else:
        # Create buy keyboard
        keyboard = [
            [InlineKeyboardButton("🛍 " + _("Buy for Me"),
                                  callback_data=f"buy_me_{promo_type}_{promo_discount}_{tour_id}")],
            [InlineKeyboardButton("🎁 " + _("Buy as gift"), callback_data=f"buy_friend_{promo_type}_{promo_discount}_{tour_id}")],
            [InlineKeyboardButton("🔙 " + _("Back to Tour List"), callback_data="buy_tours")]
        ]

    if is_owned:
        keyboard.pop(0)

    await query.message.edit_text(
        tour_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
    )
