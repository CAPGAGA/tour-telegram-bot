import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.handlers import get_current_creator
from db.database import get_session
from db.models import Rout, PromoCode, PromoCodeRout

promo_router = APIRouter(
    prefix="/promo",
    tags=["promo"],
)


class PromoCreate(BaseModel):

    code: str
    promo_type: str
    discount: str
    creator_id: str
    promo_start: Optional[str] = None
    promo_end: Optional[str] = None
    use_limit: Optional[str] = None
    routs: list[str]



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
        creator_id=promo.creator_id,
        promo_start=promo_start if promo_start else None,
        promo_end=promo_end if promo_end else None,
        use_limit=promo.use_limit
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

    return {"message": "Promo code created successfully"}

@promo_router.get("/get")
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