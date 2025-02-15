from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RoutPoint
from db.database import get_session


rout_points_router = APIRouter(
    prefix="/rout-points",
    tags=["rout-points"],
)

class RoutPointCreate(BaseModel):

    rout_id: int
    latitude: float
    longitude: float
    point_text: str


class RoutPointEdit(BaseModel):

    latitude: float
    longitude: float
    point_text: str

class RoutPointResponse(BaseModel):

    id: int
    rout_id: int
    latitude: float
    longitude: float
    point_text: str

class RoutResponse(BaseModel):

    id: int
    rout_id: int
    latitude: float
    longitude: float
    point_text: str
    image: Optional[list[str]] = None
    audio: Optional[list[str]] = None

    class Config:
        orm_mode = True



@rout_points_router.post("/create", response_model=RoutPointResponse)
async def create_rout_point(
        rout_point: RoutPointCreate,
        session: AsyncSession = Depends(get_session)
):
    new_rout_point = RoutPoint(**rout_point.dict())
    session.add(new_rout_point)
    await session.commit()
    await session.refresh(new_rout_point)
    return new_rout_point

@rout_points_router.get("/get-rout-point", response_model=RoutPointResponse)
async def get_rout_point(
        rout_point_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    rout_point = result.scalars().first()
    if not rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")
    return rout_point

@rout_points_router.get("/get-rout", response_model=list[RoutResponse])
async def get_rout(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.rout_id == rout_id)
    result = await session.execute(query)
    rout_points = result.scalars().all()

    if not rout_points:
        raise HTTPException(status_code=404, detail="Rout is empty")
    return [r.to_dict() for r in rout_points]

@rout_points_router.put('/edit-rout-point', response_model=RoutPointResponse)
async def edit_rout_point(
        rout_point_id: int,
        rout_point: RoutPointEdit,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    session_rout_point = result.scalars().first()
    if not session_rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")
    for key, value in rout_point.dict().items():
        setattr(session_rout_point, key, value)
    await session.commit()
    await session.refresh(session_rout_point)
    return session_rout_point

@rout_points_router.delete("/delete-rout-point", response_model=dict)
async def delete_rout_point(
        rout_point_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    rout_point = result.scalars().first
    if not rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")
    await session.delete(rout_point)
    await session.commit()
    return {"message": "Rout point deleted successfully"}