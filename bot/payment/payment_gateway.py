from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from settings import SUPPORTED_PAYMENT_METHODS


def get_gateway_menu(tour_id: int, subject: str, _):
    """
    Keyboard with all available payment methods.
    """

    keyboard = []
    if 'paypal' in SUPPORTED_PAYMENT_METHODS:
        keyboard.append(
            [InlineKeyboardButton(_('Pay with card'), callback_data=f'buy_world_{subject}_paypal_{tour_id}')]
        )
    if 'yuukassa_telegram' in SUPPORTED_PAYMENT_METHODS:
        keyboard.append(
            [InlineKeyboardButton(_('Pay with russian card'), callback_data=f'buy_ru_{subject}_{tour_id}')]
        )

    keyboard.append([InlineKeyboardButton('🔙' + _(' Back to Tour Page'), callback_data=f'view_tour_{subject}_{tour_id}')])

    return InlineKeyboardMarkup(keyboard)

@user_auth
async def render_gateway_menu(
        update: Update,
        context: CallbackContext,
        user
):
    """
    Render for gateway message
    """
    _ = context._

    query = update.callback_query
    await query.answer()

    tour_id, subject = int(query.data.split('_')[-1]), query.data.split('_')[1]

    await query.message.edit_text(
        _("Choose how you want to pay:"),
        reply_markup=get_gateway_menu(tour_id, subject, _),
    )
