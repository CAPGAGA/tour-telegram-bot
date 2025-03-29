from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from bot.modules.main_menu import main_menu

from bot.decorators.auth import user_auth
from bot.utils.set_language import set_language
from bot.utils.messages import send_message



@user_auth
async def start(update: Update, context: CallbackContext, user) -> None:
    """
        Sends a welcome message when the user starts the bot.
    """
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('Proceed with English', callback_data='set_language_en')],
            [InlineKeyboardButton('Продолжить на Русском', callback_data='set_language_ru')]
        ]
    )
    await send_message(
        update,
        context,
        "Hello! Welcome to the bot. Use keyboard below to set your preferred language. \n\n"
        "Привет и добро пожаловать! Используй клавиатуру снизу, чтобы установить ваш предпочитаемый язык.",
        keyboard,
        True
    )

@user_auth
async def set_language_first(
        update: Update,
        context: CallbackContext,
        user
):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[-1]

    await set_language(user['user_id'], lang)

    await main_menu(update, context)


