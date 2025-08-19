import datetime
import random
import string
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi_babel import _
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Rout, PromoCode, PromoCodeRout, Order

promo_router = APIRouter(
    prefix="/promo",
    tags=["promo"],
)


class PromoCreate(BaseModel):

    code: str
    promo_type: str
    discount: str
    creator_id: int
    promo_start: Optional[str] = None
    promo_end: Optional[str] = None
    use_limit: Optional[int] = None
    routs: list[str]

class PromoEdit(BaseModel):

    promo_id: str
    code: str
    promo_type: str
    discount: str
    creator_id: int
    promo_start: Optional[str] = None
    promo_end: Optional[str] = None
    use_limit: Optional[str] = None
    routs: list[str]

class GiftCodeCreate(BaseModel):

    invoice_id: str

@promo_router.post("/create")
async def create_promo(
    promo: PromoCreate,
    session: AsyncSession = Depends(get_session)
):
    promo_start = None
    promo_end = None

    if promo.promo_start and promo.promo_end:
        promo_start = datetime.datetime.strptime(
            promo.promo_start, "%Y-%m-%d"
        )
        promo_end = datetime.datetime.strptime(
            promo.promo_end, "%Y-%m-%d"
        )

    new_promo = PromoCode(
        code=promo.code,
        promo_type=promo.promo_type,
        discount=promo.discount,
        creator_id=int(promo.creator_id),
        promo_start=promo_start if promo_start else None,
        promo_end=promo_end if promo_end else None,
        use_limit= int(promo.use_limit) if promo.use_limit != '' else -1
    )


    session.add(new_promo)
    await session.commit()
    await session.refresh(new_promo)

    for rout_id in promo.routs:
        promo_rout = PromoCodeRout(
            promo_code_id=new_promo.id,
            rout_id=int(rout_id)
        )
        session.add(promo_rout)

    await session.commit()

    return {"message": _("Promo code created successfully")}


@promo_router.post("/create-gift")
async def create_gift_code(
        body: GiftCodeCreate,
        session: AsyncSession = Depends(get_session)
):
    #Check if order have been paid
    query = select(
        Order
    ).where(
        Order.invoice_id == body.invoice_id,
    )
    result = await session.execute(query)
    order = result.scalars().first()



    if not order:
        raise HTTPException(status_code=404, detail=_("Order not found"))

    if order.status != 'paid':
        raise HTTPException(status_code=400, detail=_("Order not paid"))

    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(15))
    new_promo = PromoCode(
        code=code,
        promo_type='percent',
        discount=str(100),
        creator_id=1,
        promo_start=datetime.datetime.now(),
        promo_end=datetime.datetime.now() + timedelta(days=365),
        use_limit=1
    )

    session.add(new_promo)
    await session.commit()

    return {"message": _("Promo code created successfully"), "code": code}

@promo_router.put("/create")
async def edit_promo(
    promo: PromoEdit,
    session: AsyncSession = Depends(get_session)
):
    query = select(PromoCode).where(PromoCode.id == int(promo.promo_id))
    result = await session.execute(query)
    promo_code = result.scalars().first()

    if not promo_code:
        raise HTTPException(status_code=404, detail="Promo code not found")

    promo_start = None
    promo_end = None

    if promo.promo_start and promo.promo_end:
        promo_start = datetime.datetime.strptime(
            promo.promo_start, "%Y-%m-%d"
        )
        promo_end = datetime.datetime.strptime(
            promo.promo_end, "%Y-%m-%d"
        )

    promo_code.code = promo.code
    promo_code.promo_type = promo.promo_type
    promo_code.discount = int(promo.discount)
    promo_code.creator_id = int(promo.creator_id)
    promo_code.promo_start = promo_start
    promo_code.promo_end = promo_end
    promo_code.use_limit = int(promo.use_limit)

    await session.commit()

    return {"message": _("Promo code updated successfully")}



@promo_router.get("/get-all")
async def get_promo(
    creator_id: int,
    session: AsyncSession = Depends(get_session)
):
    query = select(PromoCode).where(PromoCode.creator_id == creator_id)
    result = await session.execute(query)
    promo_codes = result.scalars().all()
    promos = []

    today = datetime.datetime.today()

    for promo in promo_codes:
        if promo.promo_end < today:
            promo.active = False
            promos.append(promo)
        elif promo.use_limit == 0:
            promo.active = False
            promos.append(promo)
        else:
            promo.active = True
            promos.append(promo)

    return promos

@promo_router.get("/get-promo")
async def get_promo(
    promo_id: int,
    session: AsyncSession = Depends(get_session)
):
    query = select(PromoCode).where(PromoCode.id == promo_id)
    result = await session.execute(query)
    promo = result.scalars().first()
    if promo:
        routs_query = select(
            PromoCodeRout.rout_id
        ).where(
            PromoCodeRout.promo_code_id == promo.id
        )

        routs_result = await session.execute(routs_query)
        routs = routs_result.scalars().all()
        promo.routs = routs
        return promo

@promo_router.post("/deactivate-promo")
async def deactivate_promo(
        promo_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(PromoCode).where(PromoCode.id == promo_id)
    result = await session.execute(query)
    promo = result.scalars().first()
    if promo:
        # we set timedelta to yesterday so this promo becomes unavailable
        promo.promo_end = datetime.datetime.now() - timedelta(days=1)
        await session.commit()
        return {"message": _("Promo code deactivated successfully")}

    raise HTTPException(status_code=404, detail=_("Promo code not found"))

@promo_router.post("/activate-promo")
async def activate_promo(
        code: str,
        session: AsyncSession = Depends(get_session)
):
    query = select(PromoCode).where(PromoCode.code == code)
    result = await session.execute(query)
    promo = result.scalars().first()

    if not promo:
        raise HTTPException(status_code=404, detail=_("Promo code not found"))

    routs_query = select(PromoCodeRout.rout_id).where(PromoCodeRout.promo_code_id == promo.id)
    routs_result = await session.execute(routs_query)
    routs = routs_result.scalars().all()

    today = datetime.datetime.today()

    if not (promo.promo_start < today < promo.promo_end):
        return HTTPException(status_code=400, detail=_("Promo code expired"))

    if promo.use_limit != -1:
        if promo.use_limit > 0:
            promo.use_limit -= 1

            await session.commit()
            return {
                "message": _("Promo code activated successfully"),
                "discount": promo.discount,
                "type": promo.promo_type,
                "routs": routs,
                "promo_id": promo.id
            }
        else:
            return HTTPException(status_code=400, detail=_("Promo code limit reached"))

    return {
        "message": _("Promo code activated successfully"),
        "discount": promo.discount,
        "type": promo.promo_type,
        "routs": routs,
        "promo_id": promo.id
    }
