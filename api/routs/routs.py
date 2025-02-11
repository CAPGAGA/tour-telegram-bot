from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Rout, RoutPoint


rout_router = APIRouter(
    prefix="/rout",
    tags=["rout"],
)

class RoutCreate(BaseModel):

    rout_name: str
    rout_description: str
    base_price: int


class RoutEdit(BaseModel):

    rout_name: str
    rout_description: str
    base_price: int
    is_displayed: bool

class RoutResponse(BaseModel):

    id: int
    rout_name: str
    rout_description: str
    base_price: int
    is_displayed: bool

    class Config:
        orm_mode = True



@rout_router.post("/create", response_model=RoutResponse)
async def create_rout(
        rout: RoutCreate,
        session: AsyncSession = Depends(get_session)
):
    new_rout = Rout(**rout.dict())
    session.add(new_rout)
    await session.commit()
    await session.refresh(new_rout)
    return new_rout

@rout_router.get("/get-rout/{rout_id}", response_model=RoutResponse)
async def get_rout(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    rout = result.scalars().first()
    if not rout:
        raise HTTPException(status_code=404, detail="Rout not found")
    return rout

@rout_router.put("/edit-rout/{rout_id}", response_model=RoutResponse)
async def update_rout(
        rout_id: int,
        rout: RoutEdit,
        session: AsyncSession = Depends(get_session)
):
    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    session_rout = result.scalars().first()
    if not session_rout:
        raise HTTPException(status_code=404, detail="Rout not found")
    for key, value in rout.dict().items():
        setattr(session_rout, key, value)
        session.add(session_rout)
    await session.commit()
    await session.refresh(session_rout)
    return session_rout

@rout_router.delete("/delete-rout/{rout_id}", response_model=dict)
async def delete_rout(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    rout = result.scalars().first()
    if not rout:
        raise HTTPException(status_code=404, detail="Rout not found")
    await session.delete(rout)
    await session.commit()
    return {"message": "Rout deleted successfully"}