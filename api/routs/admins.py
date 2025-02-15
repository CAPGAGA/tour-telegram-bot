from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from db.database import get_session
from db.models import AdminRout, Rout
from db.schemas import RoutSchema


admin_rout_router = APIRouter(
    prefix="/admin_rout",
    tags=["admin_rout"],
)


class AdminRoutCreate(BaseModel):

    admin_id: int
    rout_id: int

class AdminRoutResponse(BaseModel):

    admin_id: int
    routs: list[RoutSchema]

@admin_rout_router.post("/link-rout", response_model=AdminRoutResponse)
async def link_rout_to_admin(
        admin_rout: AdminRoutCreate,
        session: AsyncSession = Depends(get_session)
):

    new_admin_rout = AdminRout(**admin_rout.dict())
    session.add(new_admin_rout)
    await session.commit()
    await session.refresh(new_admin_rout)

    stmt = select(Rout).where(Rout.id == admin_rout.rout_id)
    result = await session.execute(stmt)
    rout = result.scalar_one_or_none()

    return {"admin_id": new_admin_rout.admin_id, "routs": [rout]}

@admin_rout_router.get("/get-admin-rout", response_model=AdminRoutResponse)
async def get_admin_rout(
        admin_id: int,
        session: AsyncSession = Depends(get_session)
):

    stmt = select(AdminRout).where(AdminRout.admin_id == admin_id)
    result = await session.execute(stmt)
    admin_rout = result.scalars().all()

    stmt = select(Rout).where(Rout.id.in_([rout.rout_id for rout in admin_rout]))
    result = await session.execute(stmt)
    routs = result.scalars().all()


    return {"admin_id": admin_id, "routs": [rout for rout  in routs]}

