import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# import modules
from modules.start import start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in environment variables!")


async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

# entrypoint
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error)

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()