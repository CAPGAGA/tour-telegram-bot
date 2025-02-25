from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.decorators.auth import user_auth
from bot.utils.messages import send_message

async def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 Buy Tour", callback_data="buy_tours")],
        [InlineKeyboardButton("📁 Browse My Tours", callback_data="my_tours")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("❓ About this bot", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

@user_auth
async def main_menu(update: Update, context: CallbackContext, user):
    """Displays the main menu keyboard and removes previous messages."""
    reply_markup = await get_main_menu()
    if update.message:
        # reply to command
        await send_message(
            update,
            context,
            "Main menu\n\nChoose one of the options:",
            reply_markup,
            True
        )
    if update.callback_query:
        # reply to callback
        query = update.callback_query
        await query.answer()

        await query.message.edit_text(
            "Main menu\n\nChoose one of the options:",
            reply_markup=reply_markup
        )

async def handle_menu_callbacks(
        update: Update,
        context: CallbackContext
):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_tours":
        await query.message.edit_text("💳 Here are the available tours:")
    elif query.data == 'my_tours':
        await query.message.edit_text("📁 Here are your tours:")
    elif query.data == "help":
        await query.message.edit_text("ℹ️ Need help? Contact support.")
    elif query.data == "about":
        await query.message.edit_text("❓ About this bot")