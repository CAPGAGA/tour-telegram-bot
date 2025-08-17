import aiohttp
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

from bot.decorators.auth import user_auth

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def validate_code(code):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_BASE_URL}/promo/activate-promo?code={code}") as response:
                if response.status != 200:
                    data = await response.json()
                    return data.get('detail')
                return await response.json()
        except aiohttp.ClientError:
            return None

async def get_rout(rout_id):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/rout/get-rout/{rout_id}") as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None


@user_auth
async def promo_check(
        update: Update,
        context: CallbackContext,
        user: dict
):
    query = update.callback_query
    await query.answer()

    _ = context._

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 " + _("Back to Main Menu"), callback_data="main_menu")
            ]
        ]
    )

    context.user_data['in_promo_menu'] = True
    context.user_data['original_message_id'] = query.message.message_id

    await query.message.edit_text(
        _("Please enter your promo code:"),
        reply_markup=keyboard
    )


@user_auth
async def check_code(
        update: Update,
        context: CallbackContext,
        user: dict
):
    _ = context._

    if context.user_data.get('in_promo_menu'):
        code = update.message.text.strip()
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
        except Exception as e:
            print(f"Failed to delete message: {e}")

        context.user_data.pop("in_promo_menu")
        original_message_id = context.user_data.get('original_message_id', None)

        promo = await validate_code(code)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔙 " + _("Back to Main Menu"), callback_data="main_menu")
                ]
            ]
        )

        if isinstance(promo, str):
            # If answer is str then it means that promo code is invalid
            if original_message_id:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=original_message_id,
                    text=promo,
                    reply_markup=keyboard
                )
            return
        if not promo:
            # If we get None then promo code was not found
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=original_message_id,
                text="❌ " + _("Promo code not found or invalid") + "\n\n"
                     + _("Check your promo code and try again"),
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard
            )
            return

        rout_list = []

        for rout_id in promo.get('routs'):
            rout = await get_rout(rout_id)
            calculated_price = 0.
            if promo.get('type') == 'flat':
                calculated_price = float(rout.get('base_price')) - float(promo.get('discount'))
            elif promo.get('type') == 'percent':
                calculated_price = float(rout.get('base_price')) * (1 - float(promo.get('discount')))

            rout_list.append(
                [
                    InlineKeyboardButton(
                        f"{rout.get('rout_name')} - {calculated_price}$",
                        callback_data=f"view_tour_{promo.get('type')}_{promo.get('discount')}_{rout.get('id')}"
                    )
                ]
            )

        if original_message_id:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=original_message_id,
                text="✅ " + _("Promo code activated successfully") + "\n\n"
                     + _("Below is a list of all included in promo tours:"),
                reply_markup=InlineKeyboardMarkup(rout_list),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        return





