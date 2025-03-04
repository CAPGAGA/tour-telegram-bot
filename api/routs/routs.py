import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Rout, RoutPoint, PointsAudio

from api.handlers import get_creator_id, haversine, generate_hashed_filename
from api.access_checkers import check_admin_rout_access

rout_router = APIRouter(
    prefix="/rout",
    tags=["rout"],
)

UPLOAD_IMAGE_DIR = "web/media/images"

os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)


class RoutCreate(BaseModel):

    rout_name: str
    rout_description: str
    base_price: int


class RoutEdit(BaseModel):

    rout_name: str
    rout_description: str
    base_price: int


class RoutDisplay(BaseModel):

    is_displayed: bool


class RoutResponse(BaseModel):

    id: int
    rout_name: str
    rout_description: str
    base_price: int
    is_displayed: bool
    image: Optional[str] = None

    class Config:
        orm_mode = True

class DetailedResponse(BaseModel):

    id: int
    rout_name: str
    rout_description: str
    base_price: int
    is_displayed: bool
    total_points: int
    distance: float


class DisplayedRoutsResponse(BaseModel):

    routs: list[RoutResponse]

    class Config:
        orm_mode = True



@rout_router.post("/create", response_model=RoutResponse)
async def create_rout(
        rout: RoutCreate,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_rout = Rout(**rout.dict())
    session.add(new_rout)
    await session.commit()
    await session.refresh(new_rout)
    return new_rout

@rout_router.get("/get-routs/")
async def get_routs(
        session: AsyncSession = Depends(get_session)
):
    """
    Get all displayed routs.
    """
    query = select(Rout).where(Rout.is_displayed == True)
    result = await session.execute(query)
    routs = result.scalars().all()
    return routs

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

@rout_router.get('/get-rout/detailed/{rout_id}', response_model=DetailedResponse)
async def get_rout_detailed(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    rout = result.scalars().first()

    if not rout:
        raise HTTPException(status_code=404, detail="Rout not found")

    rout_points = select(RoutPoint).where(RoutPoint.rout_id == rout.id)
    result = await session.execute(rout_points)
    points = result.scalars().all()

    if not points:
        raise HTTPException(status_code=404, detail="Rout has no points")

    total_points = len(points)
    distance = 0

    # calculate rout distance
    for i in range(total_points-1):
        distance += await haversine(points[i].longitude, points[i].latitude, points[i+1].longitude, points[i+1].latitude)

    return {
        "id": rout.id,
        "rout_name": rout.rout_name,
        "rout_description": rout.rout_description,
        "base_price": rout.base_price,
        "is_displayed": rout.is_displayed,
        "total_points": total_points,
        "distance": distance
    }


@rout_router.put("/edit-rout/{rout_id}", response_model=RoutResponse)
async def update_rout(
        rout_id: int,
        rout: RoutEdit,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_access(rout_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

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

@rout_router.post("/upload-image/{rout_id}", response_model=dict)
async def upload_rout_image(
        rout_id: int,
        image: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id),
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_access(rout_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    hashed_filename = generate_hashed_filename(image.filename)
    file_path = os.path.join(UPLOAD_IMAGE_DIR, hashed_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())

    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    rout = result.scalars().first()

    if not rout:
        raise HTTPException(status_code=404, detail="Rout not found")

    rout.image = hashed_filename
    await session.commit()

    return {"image_url": f"/media/images/{hashed_filename}", "message": "Image uploaded successfully"}




@rout_router.put("/display-rout/{rout_id}", response_model=dict)
async def display_rout(
        rout_id: int,
        rout: RoutDisplay,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_access(rout_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    db_rout = result.scalars().first()

    if not db_rout:
        raise HTTPException(status_code=404, detail="Rout not found")
    if rout.is_displayed:
        # check if rout can be displayed
        point_query = (
            select(RoutPoint.id, RoutPoint.point_text, PointsAudio.audio_name)
            .outerjoin(PointsAudio, PointsAudio.rout_point_id == RoutPoint.id)
            .where(RoutPoint.rout_id == rout_id)
        )
        point_result = await session.execute(point_query)
        points = point_result.fetchall()

        # check rout length
        if len(points) < 3:
            raise HTTPException(status_code=400, detail="Route must have at least 3 points to be displayed")

        # check text or audio presents
        for point in points:
            point_text, audio = point[1], point[2]
            if not point_text and not audio:  # If both are empty, route is invalid
                raise HTTPException(status_code=400, detail="Every route point must have either text or audio")

    # if all checks passed, update rout
    update_query = (
        update(Rout)
        .where(Rout.id == rout_id)
        .values(is_displayed=rout.is_displayed)
    )
    await session.execute(update_query)
    await session.commit()

    return {"message": "Route is now displayed"}

@rout_router.delete("/delete-rout/{rout_id}", response_model=dict)
async def delete_rout(
        rout_id: int,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_access(rout_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    query = select(Rout).where(Rout.id == rout_id)
    result = await session.execute(query)
    rout = result.scalars().first()
    if not rout:
        raise HTTPException(status_code=404, detail="Rout not found")
    await session.delete(rout)
    await session.commit()
    return {"message": "Rout deleted successfully"}