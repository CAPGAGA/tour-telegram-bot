from telegram import Update
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from bot.utils.messages import send_message

@user_auth
async def start(update: Update, context: CallbackContext, user) -> None:
    """
        Sends a welcome message when the user starts the bot.
    """
    await send_message(
        update,
        context,
        "Hello! Welcome to the bot. Use /menu to continue.",
        None,
        True
    )