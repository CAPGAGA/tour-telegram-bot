from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from db.database import get_session
from db.models import CreatorRout, Rout
from db.schemas import RoutSchema


creator_rout_router = APIRouter(
    prefix="/creator_rout",
    tags=["creator_rout"],
)


class CreatorRoutCreate(BaseModel):

    creator_id: int
    rout_id: int

class CreatorRoutResponse(BaseModel):

    creator_id: int
    routs: list[RoutSchema]

@creator_rout_router.post("/link-rout", response_model=CreatorRoutResponse)
async def link_rout_to_creator(
        creator_rout: CreatorRoutCreate,
        session: AsyncSession = Depends(get_session)
):

    new_admin_rout = CreatorRout(**creator_rout.dict())
    session.add(new_admin_rout)
    await session.commit()
    await session.refresh(new_admin_rout)

    stmt = select(Rout).where(Rout.id == creator_rout.rout_id)
    result = await session.execute(stmt)
    rout = result.scalar_one_or_none()

    return {"creator_id": new_admin_rout.creator_id, "routs": [rout]}

@creator_rout_router.get("/get-admin-rout", response_model=CreatorRoutResponse)
async def get_admin_rout(
        creator_id: int,
        session: AsyncSession = Depends(get_session)
):

    stmt = select(CreatorRout).where(CreatorRout.creator_id == creator_id)
    result = await session.execute(stmt)
    admin_rout = result.scalars().all()

    stmt = select(Rout).where(Rout.id.in_([rout.rout_id for rout in admin_rout]))
    result = await session.execute(stmt)
    routs = result.scalars().all()

    return {"creator_id": creator_id, "routs": [rout for rout  in routs]}

