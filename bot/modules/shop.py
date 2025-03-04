import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from bot.utils.messages import send_message

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

# Tours Per Page
TOURS_PER_PAGE = 5

# Store pagination state per user
USER_TOUR_PAGES = {}

async def fetch_tours():
    """Fetch available tours from API."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/rout/get-routs/") as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None

def get_tour_page_keyboard(tours, page):
    """Generate paginated tour buttons."""
    keyboard = []

    # Add tours for current page
    start = page * TOURS_PER_PAGE
    end = start + TOURS_PER_PAGE
    for tour in tours[start:end]:
        title = tour['rout_name']
        adapted_title = title if len(title) <= 30 else title[:30] + "..."
        keyboard.append([InlineKeyboardButton(f"{adapted_title} - ${tour['base_price']}", callback_data=f"view_tour_{tour['id']}")])

    # Navigation Buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"tour_page_{page - 1}"))
    if end < len(tours):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"tour_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Back to main menu
    keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)

async def show_tour_menu(update: Update, context: CallbackContext, page=0):
    """Fetch tours and display paginated menu."""
    tours = await fetch_tours()
    if not tours:
        await send_message(update, context, "❌ Failed to load tours. Try again later.", clear_previous=True)
        return

    #  Save user page state
    user_id = update.effective_user.id
    USER_TOUR_PAGES[user_id] = page

    # Show paginated tours
    if update.callback_query:
        await update.callback_query.message.edit_text("🛒 Available Tours:", reply_markup=get_tour_page_keyboard(tours, page))
    else:
        await send_message(update, context, "🛒 Available Tours:", reply_markup=get_tour_page_keyboard(tours, page), clear_previous=True)

async def handle_tour_pagination(update: Update, context: CallbackContext):
    """Handle tour page navigation."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id not in USER_TOUR_PAGES:
        USER_TOUR_PAGES[user_id] = 0

    page = int(query.data.split("_")[-1])
    await show_tour_menu(update, context, page)

async def handle_main_menu_return(update: Update, context: CallbackContext):
    """Return to main menu from tour menu."""
    from bot.modules.main_menu import main_menu
    await main_menu(update, context)