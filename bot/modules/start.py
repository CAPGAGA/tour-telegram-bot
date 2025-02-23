from telegram import Update
from telegram.ext import CallbackContext

async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the user starts the bot."""
    await update.message.reply_text("Hello! Welcome to the bot. Use /menu to continue.")