import os
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

from bot.modules.shop import show_tour_menu, handle_tour_pagination, handle_main_menu_return
from bot.modules.tour import show_tour_point
from bot.modules.tour_card import show_tour_details
from bot.modules.users_tours import users_tours
# import modules
from modules.start import start
from modules.main_menu import main_menu, handle_menu_callbacks

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
    application.add_handler(CommandHandler('menu', main_menu))
    # --- Handlers for "Buy Tours" button in main menu ---
    # Opens the tour shop list
    application.add_handler(CallbackQueryHandler(show_tour_menu, pattern="buy_tours"))
    # Used for pagination buttons
    application.add_handler(CallbackQueryHandler(handle_tour_pagination, pattern="tour_page_.*"))
    # Used to return to main menu from shop list
    application.add_handler(CallbackQueryHandler(handle_main_menu_return, pattern="main_menu"))
    # Used to open individual tour card
    application.add_handler(CallbackQueryHandler(show_tour_details, pattern="view_tour_.*"))
    # --- Handlers for "My Tours" button in main menu ---
    application.add_handler(CallbackQueryHandler(users_tours, pattern="my_tours"))
    # --- Handlers for tour ---
    application.add_handler(CallbackQueryHandler(show_tour_point, pattern="start_mytour_.*"))
    application.add_handler(CallbackQueryHandler(show_tour_point, pattern="end_mytour_.*"))
    application.add_handler(CallbackQueryHandler(show_tour_point, pattern="mid_mytour_.*"))

    application.add_error_handler(error)

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()