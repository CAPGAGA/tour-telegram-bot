from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.sync import update
from starlette.responses import RedirectResponse

from db.database import get_session
from db.models import Rout, BaseUser, UserRout, Order

from api.handlers import decode_payment_token
from api.invoice_constructor import InvoiceConstructor

order_router = APIRouter(
    prefix="/order",
    tags=["order"],
)

class OrderCreate(BaseModel):

    user_id: int
    rout_id: int

class OrderResponse(BaseModel):

    order_id: int
    payment_link: str


@order_router.post('/create/paypal', response_model=OrderResponse)
async def create_order_paypal(
        order: OrderCreate,
        session: AsyncSession = Depends(get_session)
):
    invoice_data = await InvoiceConstructor.return_invoice_paypal_link(
        order.rout_id,
        order.user_id,
        session
    )
    # create order in db
    new_order = Order(
        user_id = order.user_id,
        rout_id = order.rout_id,
        amount = invoice_data['amount'],
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
        raise HTTPException(status_code=500, detail="Failed to decode payment token")

    result = await session.execute(
        select(Order).where(Order.invoice_id == invoice_id)
    )
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order does not exists")

    order.status = 'paid'
    await session.commit()

    result = await session.execute(
        select(UserRout).where(UserRout.user_id == user_id, UserRout.rout_id == tour_id)
    )
    user_rout = result.scalars().first()

    if not user_rout:
        new_user_rout = UserRout(user_id=user_id, rout_id=tour_id)
        session.add(new_user_rout)
        session.commit()

    return RedirectResponse(url='/')

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

    return RedirectResponse(url='/')