import os

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from bot.utils.messages import send_message

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")


async def fetch_user_routs(user_id):
    """Fetch tours owned by a specific user"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/user_routs/get-user-rout", params={"user_id": user_id}) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None


@user_auth
async def users_tours(update: Update, context: CallbackContext, user):
    """Displays a list of routes owned by the user"""
    user_id = user["id"]
    routs = await fetch_user_routs(user_id)

    if not routs:
        keyboard = [
            [InlineKeyboardButton("🛒 Buy your first tour", callback_data="buy_tours")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.message.edit_text("❌ You have no purchased routes yet.", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        await send_message(
            update,
            context,
            "❌ You have no purchased routes yet.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            clear_previous=True
        )
        return

    # Generate inline buttons for user’s routes
    keyboard = [[InlineKeyboardButton(route["rout_name"], callback_data=f"start_mytour_{route['id']}")] for route in routs]
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "📁 Your Purchased Routes:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await send_message(update, context, "📁 Your Purchased Routes:", clear_previous=True)
    await update.message.reply_text(
        "Select a tour to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return