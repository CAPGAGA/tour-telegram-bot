from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.decorators.auth import user_auth
from bot.utils.messages import send_message

async def get_main_menu(_):
    keyboard = [
        [InlineKeyboardButton("🛒 "+ _("Buy Tour"), callback_data="buy_tours")],
        [InlineKeyboardButton("📁 " + _("Browse My Tours"), callback_data="my_tours")],
        [InlineKeyboardButton("ℹ️ " + _("Help"), callback_data="help")],
        [InlineKeyboardButton("❓ " + _("About this bot"), callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

@user_auth
async def main_menu(
        update: Update,
        context: CallbackContext,
        user
):
    """Displays the main menu keyboard and removes previous messages."""

    _ = context._

    reply_markup = await get_main_menu(_)
    if update.message:
        # reply to command
        await send_message(
            update,
            context,
            _("Main menu\n\nChoose one of the options:"),
            reply_markup,
            True
        )
    if update.callback_query:
        # reply to callback
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            _("Main menu\n\nChoose one of the options:"),
            reply_markup=reply_markup
        )
