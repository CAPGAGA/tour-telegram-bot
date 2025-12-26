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

    # Parse callback data
    _, _, promo_type, promo_discount, tour_id = query.data.split("_")

    tour = await fetch_tour_details(tour_id)
    user_tours = await fetch_users_tours(user.get("id"))
    is_owned = False

    if user_tours:
        for user_tour in user_tours:
            if user_tour['rout_id'] == int(tour_id):
                is_owned = True
                break

    if not tour:
        keyboard = [[InlineKeyboardButton("🛒 " + _("Back to shop"), callback_data="buy_tours")]]
        await query.message.edit_text(
            "❌ " + _("Failed to load tour details. Try again later."),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    rout_name_raw = tour["rout_name"]
    description_raw = tour["rout_description"]
    points_raw = tour["total_points"]

    base_price_raw = float(str(tour["base_price"]).replace("\\", ""))
    distance_raw = round(float(tour["distance"]), 2)

    final_price_raw = base_price_raw

    if promo_type != "None" and promo_discount != "None":
        promo_discount_raw = float(promo_discount.replace("\\", ""))

        if promo_type == "flat":
            final_price_raw = max(0, base_price_raw - promo_discount_raw)

        elif promo_type == "percent":
            final_price_raw = max(0, base_price_raw * (1 - promo_discount_raw / 100))


    rout_name = escape_markdown(rout_name_raw, version=2)
    description = escape_markdown(description_raw, version=2)
    points = escape_markdown(str(points_raw), version=2)
    distance = escape_markdown(str(distance_raw), version=2)

    base_price = escape_markdown(str(round(base_price_raw, 2)), version=2)
    final_price = escape_markdown(str(round(final_price_raw, 2)), version=2)

    if promo_type != "None" and promo_discount != "None":
        tour_text = (
            f"🗺 **{rout_name}**"
            f"\n💰 **{_('Your Price')}:** {final_price}$"
            f"\n\n📖 **{_('Description')}:** {description}"
            f"\n\n📢 **{_('Points')}:** {points} ┃ "
            f"📏 **{_('Distance')}:** {distance} km"
        )
    else:
        tour_text = (
            f"🗺 **{rout_name}**"
            f"\n\n💵 **{_('Price')}:** {base_price}$"
            f"\n\n📖 **{_('Description')}:** {description}"
            f"\n\n📢 **{_('Points')}:** {points} ┃ "
            f"📏 **{_('Distance')}:** {distance} km"
        )

    if final_price_raw == 0:
        keyboard = [
            [InlineKeyboardButton("➕ " + _("Add to My Account"), callback_data=f"add_tour_{tour_id}")],
            [InlineKeyboardButton("🔙 " + _("Back to Tour List"), callback_data="buy_tours")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(
                "🛍 " + _("Buy for Me"),
                callback_data=f"buy_me_{promo_type}_{promo_discount}_{tour_id}"
            )],
            [InlineKeyboardButton(
                "🎁 " + _("Buy as gift"),
                callback_data=f"buy_friend_{promo_type}_{promo_discount}_{tour_id}"
            )],
            [InlineKeyboardButton("🔙 " + _("Back to Tour List"), callback_data="buy_tours")]
        ]

    if is_owned and keyboard:
        keyboard.pop(0)

    await query.message.edit_text(
        tour_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
    )
