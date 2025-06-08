import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from db.database import get_session
from db.models import Rout, BaseUser, UserRout, Order

from api.utils.handlers import decode_payment_token
from api.utils.invoice_constructor import InvoiceConstructor

logger = logging.getLogger(__name__)

payment_error = "/payment/error"
payment_success = "/payment/success"
payment_cancel = "/payment/cancel"

order_router = APIRouter(
    prefix="/order",
    tags=["order"],
)

class FreeOrderCreate(BaseModel):

    user_id: int
    rout_id: int


class OrderCreate(BaseModel):

    user_id: int
    rout_id: int
    discount_type: Optional[str] = "None"
    discount_value: Optional[str] = "None"


class OrderResponsePayPal(BaseModel):

    order_id: int
    payment_link: str

class OrderResponseTelegram(BaseModel):

    order_id: int
    order_sign: str
    invoice_payload: dict


@order_router.post('/create/paypal', response_model=OrderResponsePayPal)
async def create_order_paypal(
        order: OrderCreate,
        session: AsyncSession = Depends(get_session)
):
    invoice_data = await InvoiceConstructor.return_invoice_paypal_link(
        order.rout_id,
        order.user_id,
        order.discount_type,
        order.discount_value,
        session
    )
    # create order in db
    new_order = Order(
        user_id = order.user_id,
        rout_id = order.rout_id,
        amount = str(invoice_data['amount']),
        payment_method = invoice_data['payment_method'],
        invoice_id = invoice_data['invoice_id'],
        payment_link = invoice_data['approval_link']
    )
    session.add(new_order)
    await session.commit()

    return {
        "order_id": new_order.id,
        "payment_link": invoice_data['approval_link']
    }

@order_router.get('/complete/paypal/success/{token}')
async def complete_order_paypal_success(
        token: str,
        session: AsyncSession = Depends(get_session)
):
    user_id, tour_id, invoice_id = decode_payment_token(token)

    if not user_id or not tour_id or not invoice_id:
        logger.error("Failed to decode payment token")
        return RedirectResponse(url=payment_error)

    result = await session.execute(
        select(Order).where(Order.invoice_id == invoice_id)
    )
    order = result.scalars().first()

    if not order:
        logger.error("Order does not exists")
        return RedirectResponse(url=payment_error)

    order.status = 'paid'
    await session.commit()

    result = await session.execute(
        select(UserRout).where(UserRout.user_id == user_id, UserRout.rout_id == tour_id)
    )
    user_rout = result.scalars().first()

    if not user_rout:
        new_user_rout = UserRout(user_id=user_id, rout_id=tour_id)
        session.add(new_user_rout)
        await session.commit()

    return RedirectResponse(url=payment_success)

@order_router.get('/complete/paypal/cancel/{token}')
async def complete_order_paypal_cancel(
        token: str,
        session: AsyncSession = Depends(get_session)
):
    user_id, tour_id, invoice_id = decode_payment_token(token)

    if not user_id or not tour_id or not invoice_id:
        raise HTTPException(status_code=500, detail="Failed to decode payment token")

    result = await session.execute(
        select(Order).where(Order.invoice_id == invoice_id)
    )
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order does not exists")

    order.status = 'canceled'
    await session.commit()

    return RedirectResponse(url=payment_cancel)

@order_router.post('/create/youkassa', response_model=OrderResponseTelegram)
async def create_order_youkassa(
        order: OrderCreate,
        session: AsyncSession = Depends(get_session)
):
    invoice_data = await InvoiceConstructor.return_invoice_telegram_json(
        order.user_id,
        order.rout_id,
        order.discount_type,
        order.discount_value,
        session
    )

    # create order in db
    new_order = Order(
        user_id=order.user_id,
        rout_id=order.rout_id,
        amount=str(invoice_data['amount']),
        payment_method=invoice_data['payment_method'],
        invoice_id=invoice_data['invoice_id'],
        payment_link=None
    )
    session.add(new_order)
    await session.commit()

    return {
        "order_id": new_order.id,
        "order_sign": invoice_data['order_sign'],
        "invoice_payload": invoice_data['invoice_payload']
    }

@order_router.post('/complete/youkassa/success/{token}')
async def complete_order_youkassa_success(
        token: str,
        session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Order).where(Order.invoice_id == token)
        )
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order does not exists")

    order.status = 'paid'
    await session.commit()

    result = await session.execute(
        select(UserRout).where(UserRout.user_id == order.user_id, UserRout.rout_id == order.rout_id)
    )
    user_rout = result.scalars().first()

    if not user_rout:
        new_user_rout = UserRout(user_id=order.user_id, rout_id=order.rout_id)
        session.add(new_user_rout)
        await session.commit()

    return Response(status_code=200, content='ok')

@order_router.post('/complete/free')
async def create_free_order(
        order: FreeOrderCreate,
        session: AsyncSession = Depends(get_session)
):

    result = await session.execute(
        select(Rout).where(Rout.id == order.rout_id)
    )
    rout = result.scalars().first()

    if not rout:
        raise HTTPException(status_code=404, detail="Rout does not exists")

    result = await session.execute(
        select(BaseUser).where(BaseUser.id == order.user_id)
        )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User does not exists")

    new_order = Order(
        user_id=order.user_id,
        rout_id=order.rout_id,
        amount=0,
        payment_method='Free',
        invoice_id=f'Free_{order.user_id}_{order.rout_id}',
        payment_link=None
    )

    session.add(new_order)
    await session.commit()

    result = await session.execute(
        select(UserRout).where(UserRout.user_id == user.id, UserRout.rout_id == order.rout_id)
    )
    user_rout = result.scalars().first()

    if not user_rout:
        new_user_rout = UserRout(user_id=user.id, rout_id=order.rout_id)
        session.add(new_user_rout)
        await session.commit()

    return {
        "order_id": new_order.id,
    }
