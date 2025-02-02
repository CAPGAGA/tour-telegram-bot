import copy
from typing import Union, Dict
from decimal import Decimal

from telegram import LabeledPrice

from settings import PAYMENT_TOKEN

# for telegram payment
default_provider_data = {
    "receipt": {
        "items": [
            {
                "description": 'Доступ к боту "дашины маршруты" для друга',
                "quantity": "1.00",
                "amount" :
                    {
                        "value": "1400.00",
                        "currency": "RUB"
                    },
                "vat_code" : 1
            }

        ]
    }
}

tg_invoice = {
    "description": "Доступ к закрытому телеграм-боту "
                   "с маршрутом по городу, в который "
                   "входят отмеченные на карте точки "
                   "и аудио- и фотоматериалы к каждой из них.",
    "payload": "Custom-Payload",
    "currency": "RUB",
    "need_name": False,
    "need_phone_number": False,
    "is_flexible": False,
    "provider_token": PAYMENT_TOKEN,
    "need_email": True,
    "send_email_to_provider": True,
}

# for prodamus payment
default_prodamus_invoice = {
    'products': [
        {
            'name': 'Доступ к материалам бота',
            'price': '7069',
            'quantity': '1',
            'tax': {
                'tax_type': 0,
            },
        },
    ],
    'do': 'pay',
    "sys": "bakeshop",
    'paid_content': 'Спасибо!',
    'currency': 'kzt',
    'payments_limit': 1,
}


async def prepare_payment_invoice(
        payment_type: str,
        payment_reason: str,
        discount_type: str = None,
        discount: Union[int, float] = None,
) -> Dict:
    """
    Function to create telegram and prodamus payment invoices
    :param payment_type:
    :param payment_reason:
    :param discount_type:
    :param discount:
    :param chat_id:
    :param secure_hash:
    :return:
    """
    if payment_type == "ru_card":
        # preparing invoice for russian cards
        if payment_reason == "self":
            # preparing invoice for payment for self
            if discount_type:
                # applying discount
                if discount_type == "is_percent":
                    # for ru cards discount applies to 1400 RUB
                    discounted_price = Decimal("1400") * (Decimal("1") - Decimal(f"0.{discount}"))
                elif discount_type == "not_percent":
                    discounted_price = discount
                else:
                    raise ValueError(f"Unknown discount type: {discount_type}")
                # update provider data
                provider_data_with_discount = copy.deepcopy(default_provider_data)
                provider_data_with_discount["receipt"]["items"][0]["amount"]["value"] = f"{discounted_price}"
                # update telegram invoice data
                new_tg_invoice = copy.deepcopy(tg_invoice)
                new_tg_invoice["title"] = "Доступ к боту (ПРОМО)"
                new_tg_invoice["provider_data"] = provider_data_with_discount
                new_tg_invoice["prices"] = [LabeledPrice('Доступ к боту', int(discounted_price) * 100)]

                return new_tg_invoice
            else:
                # copy default provider data
                provider_data_no_discount = copy.deepcopy(default_provider_data)
                # update telegram invoice data
                new_tg_invoice = copy.deepcopy(tg_invoice)
                new_tg_invoice["title"] = "Доступ к боту"
                new_tg_invoice["provider_data"] = provider_data_no_discount
                new_tg_invoice["prices"] = [LabeledPrice('Доступ к боту', 1400 * 100)]
                return new_tg_invoice
        elif payment_reason == "friend":
            # preparing invoice for certificate
            # copy default provider data
            provider_data = copy.deepcopy(default_provider_data)
            # update telegram invoice data
            new_tg_invoice = copy.deepcopy(tg_invoice)
            new_tg_invoice["title"] = "Доступ к боту для друга"
            new_tg_invoice["provider_data"] = provider_data
            new_tg_invoice["prices"] = [LabeledPrice('Доступ к боту', 1400 * 100)]
            return new_tg_invoice
    elif payment_type == "noru_card":
        # preparing invoice for rest of the world cards
        if payment_reason == "self":
            # preparing invoice for payment for self
            if discount_type:
                # applying discount
                if discount_type == "is_percent":
                    # for not ru cards discount applies to 17 USD
                    discounted_price = Decimal("7069") * (Decimal("1") - Decimal(f"0.{discount}"))
                elif discount_type == "not_percent":
                    discounted_price = Decimal(str(discount)) * Decimal("5,05")
                else:
                    raise ValueError(f"Unknown discount type: {discount_type}")
                # update prodamus invoice data
                prodamus_invoice_with_discount = copy.deepcopy(default_prodamus_invoice)
                prodamus_invoice_with_discount["products"][0]['price'] = discounted_price

                return prodamus_invoice_with_discount
            else:
                prodamus_invoice_no_discount = copy.deepcopy(default_prodamus_invoice)

                return prodamus_invoice_no_discount
        elif payment_reason == "friend":
            # preparing invoice for certificate
            if discount_type:
                # applying discount
                if discount_type == "is_percent":
                    # for not ru cards discount applies to 17 USD
                    discounted_price = Decimal("7069") * (Decimal("1") - Decimal(f"0.{discount}"))
                elif discount_type == "not_percent":
                    discounted_price = Decimal(str(discount)) * Decimal("5,05")
                else:
                    raise ValueError(f"Unknown discount type: {discount_type}")
                # update prodamus invoice data
                prodamus_invoice_with_discount = copy.deepcopy(default_prodamus_invoice)
                prodamus_invoice_with_discount["products"][0]['price'] = discounted_price

                return prodamus_invoice_with_discount
            else:
                prodamus_invoice_no_discount = copy.deepcopy(default_prodamus_invoice)

                return prodamus_invoice_no_discount
    else:
        raise ValueError(f"Unknown payment method: {payment_type}")