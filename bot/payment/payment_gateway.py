import logging
import os

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from settings import SUPPORTED_PAYMENT_METHODS

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

logger = logging.getLogger(__name__)

def get_gateway_menu(
        tour_id: int,
        subject: str,
        promo_type: str,
        discount: str,
        _):
    """
    Keyboard with all available payment methods.
    """

    keyboard = []
    if 'paypal' in SUPPORTED_PAYMENT_METHODS:
        keyboard.append(
            [InlineKeyboardButton(_('Pay with card'), callback_data=f'buy_world_{promo_type}_{discount}_{subject}_paypal_{tour_id}')]
        )
    if 'yuukassa_telegram' in SUPPORTED_PAYMENT_METHODS:
        keyboard.append(
            [InlineKeyboardButton(_('Pay with russian card'), callback_data=f'buy_ru_{promo_type}_{discount}_{subject}_youkassa_{tour_id}')]
        )

    keyboard.append([InlineKeyboardButton('🔙' + _(' Back to Tour Page'), callback_data=f'view_tour_None_None_{tour_id}')])

    return InlineKeyboardMarkup(keyboard)

@user_auth
async def render_gateway_menu(
        update: Update,
        context: CallbackContext,
        user
):
    """
    Render for gateway message
    """
    _ = context._

    query = update.callback_query
    await query.answer()

    data = query.data.split('_')

    tour_id = int(data[-1])
    promo_discount = data[-2]
    promo_type = data[-3]
    subject = data[-4]

    await query.message.edit_text(
        _("Choose how you want to pay:"),
        reply_markup=get_gateway_menu(tour_id, subject, promo_type, promo_discount, _),
    )

@user_auth
async def free_add_rout(
        update: Update,
        context: CallbackContext,
        user
):
    """
    Render confirming message that tour is added for free
    """
    _ = context._

    query = update.callback_query
    await query.answer()

    tour_id = query.data.split("_")[-1]

    try:
        # Call API to add tour to user's account
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/complete/free"
            payload = {
                "user_id": user.get("id"),
                "tour_id": int(tour_id)
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    await query.message.edit_text(
                        "✅ " + _("Tour successfully added to your account!"),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🛒 " + _("Back to shop"), callback_data="buy_tours")],
                            [InlineKeyboardButton("📚 " + _("My Tours"), callback_data="my_tours")]
                        ])
                    )
                else:
                    await query.message.edit_text(
                        "❌ " + _("Failed to add tour to your account. Please try again later."),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔄 " + _("Try Again"), callback_data=f"add_tour_{tour_id}")],
                            [InlineKeyboardButton("🛒 " + _("Back to shop"), callback_data="buy_tours")]
                        ])
                    )
    except Exception as e:
        logger.error(f"Error adding free tour to account: {e}")
        await query.message.edit_text(
            "❌ " + _("An error occurred. Please try again later."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 " + _("Try Again"), callback_data=f"add_tour_{tour_id}")],
                [InlineKeyboardButton("🛒 " + _("Back to shop"), callback_data="buy_tours")]
            ])
        )


