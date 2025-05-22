import os
import logging


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import CallbackContext, CallbackQueryHandler

from bot.payment.utils import fetch_tour_payment_details, complete_order, get_gift_code
from bot.decorators.auth import user_auth

# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

logger = logging.getLogger(__name__)

async def construct_invoice(
        chat_id: int,
        data: dict,
        _
):
    """
        Fetch raw invoice data and transforms it into telegram invoice
    """
    invoice_data = await fetch_tour_payment_details(
        user_id=data['user_id'],
        tour_id=data['tour_id'],
        method=data['method'],
        subject=data['subject'],
        discount=data['discount'],
        promo_type=data['promo_type']
    )
    if not invoice_data:
        return None

    price = int(float(invoice_data['invoice_payload']["prices"]['price']) * 100)

    prices = [
        LabeledPrice(
            label=invoice_data['invoice_payload']["prices"]['label'],
            amount=price
        )
    ]

    keyboard = [
        [InlineKeyboardButton(_("Pay"), pay=True)],
        [InlineKeyboardButton("❌" + _(" Cancel Payment"), callback_data=f"cancel_payment_{data['tour_id']}")],
    ]

    provider_data = {
        "receipt": {
            "items": [
                {
                    "description": invoice_data['invoice_payload']['description'],
                    "quantity": "1.00",
                    "amount": {
                        "value": str(price / 100),
                        "currency": invoice_data['invoice_payload']['currency']
                    },
                    "vat_code": 1,
                    "payment_mode": "full_payment"
                }
            ]
        }
    }

    invoice = {
        'chat_id': chat_id,
        'title': invoice_data['invoice_payload']['title'],
        'description': invoice_data['invoice_payload']['description'],
        'provider_token': invoice_data['invoice_payload']['provider_token'],
        'is_flexible': invoice_data['invoice_payload']['is_flexible'],
        'currency': invoice_data['invoice_payload']['currency'],
        'prices': prices,
        'payload': invoice_data['invoice_payload']['payload'],
        'need_email': invoice_data['invoice_payload']['need_email'],
        'need_phone_number': invoice_data['invoice_payload']['need_phone_number'],
        'send_email_to_provider': invoice_data['invoice_payload']['send_email_to_provider'],
        'send_phone_number_to_provider': invoice_data['invoice_payload']['send_phone_number_to_provider'],
        'provider_data': provider_data,
        'protect_content': invoice_data['invoice_payload']['protect_content'],
        'reply_markup': InlineKeyboardMarkup(keyboard)
    }
    print(invoice)
    return invoice

@user_auth
async def redner_youkassa_payment_menu(
        update: Update,
        context: CallbackContext,
        user: dict
):
    """
        Renders and sends the YouKassa payment menu.
    """
    _ = context._

    query = update.callback_query
    await query.answer()

    # extract needed for invoice data
    tour_id = query.data.split("_")[-1]
    method = query.data.split("_")[-2]
    subject = query.data.split("_")[-3]
    discount = query.data.split("_")[-4]
    promo_type = query.data.split("_")[-5]

    data = {
        "user_id": user['id'],
        "tour_id": tour_id,
        "method": method,
        "subject": subject,
        "discount": discount,
        "promo_type": promo_type
    }

    invoice = await construct_invoice(update.effective_chat.id, data, _)

    if not invoice:
        keyboard = [[InlineKeyboardButton('🛒' + _('Back to tour page'), callback_data=f"view_tour_{promo_type}_{discount}_{tour_id}")]]
        await query.message.edit_text(
            "❌ " + _("Failed to generate payment details. Try again later."),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await context.bot.send_invoice(
        **invoice
    )
    context.user_data['buying_for'] = subject
    return


async def pre_checkout_handler(update: Update, context: CallbackContext):
    """Handles the pre-checkout query and approves it."""
    query = update.pre_checkout_query
    await query.answer(ok=True)

@user_auth
async def successful_payment_handler(
        update: Update,
        context: CallbackContext,
        user
):
    """
    Handles successful payment and sends to my-tours
    """
    _ = context._

    payment = update.message.successful_payment
    payment_token = payment.invoice_payload
    subject = context.user_data['buying_for']
    del(context.user_data['buying_for'])



    completed = await complete_order(
        method='youkassa',
        token=payment_token
    )

    if completed:
        keyboard = [
            [InlineKeyboardButton('🛒 ' + _('Shop more'), callback_data='buy_tours')],
            [InlineKeyboardButton('🔙 ' + _('To your tours'), callback_data='my_tours')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if subject == 'friend':
            gift_code = await get_gift_code(payment_token)
            if not gift_code:
                keyboard = [
                    [InlineKeyboardButton('🔙 Return to Main Menu', callback_data='main_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                contact_info = (f"⚠️ " + _("Payment successful, but order confirmation failed.") + "\n\n" +
                                f"📞 " + _("Contact Support: @your_support") + "\n\n" +
                                _("Your payment token") + f": {payment_token}")
                await update.message.reply_text(contact_info, reply_markup=reply_markup)

            await update.message.reply_text("✅ " + _("Payment successful! Your order has been confirmed.") +
                                            "\n" + _("Here is your gift code: ") + "<b>" + gift_code['code'] + "</b>" + "\n\n" +
                                            _('Your friend may activate it by submitting this code in "Enter Promo Code" button in main menu'),
                                            reply_markup=reply_markup,
                                            parse_mode='html'
                                            )
            return



        await update.message.reply_text("✅ " + _("Payment successful! Your order has been confirmed."),
                                        reply_markup=reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton('🔙 Return to Main Menu', callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        contact_info = (f"⚠️ " + _("Payment successful, but order confirmation failed.") + "\n\n" +
                        f"📞 " + _("Contact Support: @your_support") + "\n\n" +
                        _("Your payment token") + f": {payment_token}")
        await update.message.reply_text(contact_info, reply_markup=reply_markup)

@user_auth
async def handle_cancel_payment(
        update: Update,
        context: CallbackContext,
        user
):
    _ = context._
    query = update.callback_query
    await query.answer()

    tour_id = query.data.split('_')[-1]

    # Delete the invoice message
    try:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    except Exception as e:
        logger.error(f"Failed to delete invoice message: {e}")

    # Send cancellation confirmation
    keyboard = [[InlineKeyboardButton("🔙 " + _("Return to tour page"), callback_data=f"view_tour_None_None_{tour_id}")]]
    await query.message.reply_text(
        "❌ " + _("Payment has been canceled."),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )