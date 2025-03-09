import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import CallbackContext, CallbackQueryHandler

from bot.payment.utils import fetch_tour_payment_details
from bot.decorators.auth import user_auth
from bot.utils.messages import send_message


# API Base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def construct_invoice(
        chat_id: int,
        data: dict
):
    """
        Fetch raw invoice data and transforms it into telegram invoice
    """
    invoice_data = await fetch_tour_payment_details(
        user_id=data['user_id'],
        tour_id=data['tour_id'],
        method='telegram'
    )
    if not invoice_data:
        return None

    prices = [
        LabeledPrice(
            label=invoice_data['invoice_payload']["prices"]['label'],
            amount=int(float(invoice_data['invoice_payload']["prices"]['price']) * 100)
        )
    ]

    invoice = {
        'chat_id': chat_id,
        'title': invoice_data['invoice_payload']['title'],
        'description': invoice_data['invoice_payload']['description'],
        'provider_token': invoice_data['invoice_payload']['provider_token'],
        'is_flexible': invoice_data['invoice_payload']['is_flexible'],
        'currency': invoice_data['invoice_payload']['currency'],
        'prices': prices,
        'starter_parameter': invoice_data['order_sign'],
        'need_email': invoice_data['invoice_payload']['need_email'],
        'need_phone_number': invoice_data['invoice_payload']['need_phone_number'],
        'send_email_to_provider': invoice_data['invoice_payload']['send_email_to_provider'],
        'send_phone_number_to_provider': invoice_data['invoice_payload']['send_phone_number_to_provider'],
        'protect_content': invoice_data['invoice_payload']['protect_content']
    }
    return {}

@user_auth
async def redner_youkassa_payment_menu(
        update: Update,
        context: CallbackContext,
        user: dict
):
    raise NotImplementedError