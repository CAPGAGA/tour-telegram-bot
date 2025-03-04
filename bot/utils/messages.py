from telegram import Update
from telegram.ext import CallbackContext

# todo: move to persistent storage
LAST_MESSAGES = {}

async def send_message(update: Update, context: CallbackContext, text: str, reply_markup = None, clear_previous=False):
    """Sends a message and deletes the previous one if needed."""
    chat_id = update.effective_chat.id

    # Clear the previous message if it exists
    if clear_previous and chat_id in LAST_MESSAGES:
        try:
            await context.bot.delete_message(chat_id, LAST_MESSAGES[chat_id])
        except Exception:
            pass  # Ignore errors if the message was already deleted

    # Send a new message and store its ID
    if reply_markup:
        message = await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        message = await update.message.reply_text(text)
    LAST_MESSAGES[chat_id] = message.message_id