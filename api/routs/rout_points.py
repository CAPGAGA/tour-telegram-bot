from collections import defaultdict
from typing import Optional, Any
from typing_extensions import Self

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RoutPoint, PointMedia, PointsAudio
from db.database import get_session

from api.handlers import get_creator_id
from api.access_checkers import check_admin_rout_point_access


rout_points_router = APIRouter(
    prefix="/rout-points",
    tags=["rout-points"],
)

class RoutPointCreate(BaseModel):

    rout_id: int
    latitude: float
    longitude: float
    point_text: Optional[str] = None


class RoutPointEdit(BaseModel):

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    point_text: Optional[str] = None

class RoutPointResponse(BaseModel):

    id: int
    rout_id: int
    latitude: float
    longitude: float
    point_text: str
    image: Optional[list[str]] = None
    audio: Optional[list[str]] = None

class DetailedRoutPointResponse(BaseModel):

    id: int
    rout_id: int
    latitude: float
    longitude: float
    point_text: str
    image: Optional[list[str]] = None
    audio: Optional[list[str]] = None
    next_point: Optional[int] = None



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
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_rout_point = RoutPoint(**rout_point.dict())
    session.add(new_rout_point)
    await session.commit()
    await session.refresh(new_rout_point)
    return new_rout_point

@rout_points_router.get("/get-first-point", response_model=DetailedRoutPointResponse)
async def get_first_point(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.rout_id == rout_id).limit(1)
    result = await session.execute(query)
    first_point = result.scalars().first()

    if not first_point:
        raise HTTPException(status_code=404, detail="Rout is empty")

    point_media = await session.execute(select(PointMedia).where(PointMedia.rout_point_id == first_point.id))
    first_point.image = [media.media_name for media in point_media.scalars().all()]

    point_audio = await session.execute(select(PointsAudio).where(PointsAudio.rout_point_id == first_point.id))
    first_point.audio = [media.audio_name for media in point_audio.scalars().all()]

    next_point = select(RoutPoint).where(
        RoutPoint.rout_id == first_point.rout_id,
        RoutPoint.id > first_point.id
    ).limit(1)
    result = await session.execute(next_point)
    next_point = result.scalars().first()

    first_point.next_point = next_point.id if next_point else None

    return first_point


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

    point_media = await session.execute(select(PointMedia).where(PointMedia.rout_point_id == rout_point_id))
    rout_point.image = [media.media_name for media in point_media.scalars().all()]

    point_audio = await session.execute(select(PointsAudio).where(PointsAudio.rout_point_id == rout_point_id))
    rout_point.audio = [media.audio_name for media in point_audio.scalars().all()]

    return rout_point

@rout_points_router.get("/get-detailed-rout-point", response_model=DetailedRoutPointResponse)
async def get_detailed_rout_point(
        rout_point_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    rout_point = result.scalars().first()

    if not rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")

    point_media = await session.execute(select(PointMedia).where(PointMedia.rout_point_id == rout_point_id))
    rout_point.image = [media.media_name for media in point_media.scalars().all()]

    point_audio = await session.execute(select(PointsAudio).where(PointsAudio.rout_point_id == rout_point_id))
    rout_point.audio = [media.audio_name for media in point_audio.scalars().all()]

    next_point = select(RoutPoint).where(
        RoutPoint.rout_id == rout_point.rout_id,
        RoutPoint.id > rout_point.id
    ).limit(1)
    result = await session.execute(next_point)
    next_point = result.scalars().first()

    rout_point.next_point = next_point.id if next_point else None

    return rout_point

@rout_points_router.get("/get-rout", response_model=list[RoutResponse])
async def get_rout(
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = (
        select(
            RoutPoint,
            PointMedia.media_name,
            PointsAudio.audio_name
        )
        .join(PointMedia, PointMedia.rout_point_id == RoutPoint.id, isouter=True)
        .join(PointsAudio, PointsAudio.rout_point_id == RoutPoint.id, isouter=True)
        .where(RoutPoint.rout_id == rout_id)
    )
    result = await session.execute(query)
    rows = result.fetchall()

    point_map = defaultdict(
        lambda: {
            "id": None,
            "rout_id": None,
            "latitude": None,
            "longitude": None,
            "point_text": None,
            "image": set(), # important to delete duplicates
            "audio": set() # important to remove duplicates
        }
    )

    for row in rows:
        point: RoutPoint = row[0]
        point_id = point.id
        if not point_map[point_id]["id"]:
            point_map[point_id].update(
                **{
                    "id": point.id,
                    "rout_id": point.rout_id,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "point_text": point.point_text
                }
            )

        # recombine media and audio data into lists
        if row[1] and f'media/audio/{row[1]}' not in point_map[point_id]["image"]:  # Image
            point_map[point_id]["image"].add(f'media/images/{row[1]}')

        if row[2] and f'media/audio/{row[2]}' not in point_map[point_id]["audio"]:  # Audio
            point_map[point_id]["audio"].add(f'media/audio/{row[2]}')

    # Convert sets to lists before returning
    rout_points = list(point_map.values())

    if not rout_points:
        raise HTTPException(status_code=404, detail="Rout is empty")
    return rout_points

@rout_points_router.put('/edit-rout-point', response_model=RoutPointResponse)
async def edit_rout_point(
        rout_point_id: int,
        rout_point: RoutPointEdit,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_point_access(rout_point_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    # Fetch the route point
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    session_rout_point = result.scalars().first()

    if not session_rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")

    # exclude all none values from update
    update_data = rout_point.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session_rout_point, key, value)

    await session.commit()
    await session.refresh(session_rout_point)
    return session_rout_point

@rout_points_router.delete("/delete-rout-point", response_model=dict)
async def delete_rout_point(
        rout_point_id: int,
        session: AsyncSession = Depends(get_session),
        creator_id: int = Depends(get_creator_id)
):
    if not creator_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_point_access(rout_point_id, creator_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    # Fetch the route point
    query = select(RoutPoint).where(RoutPoint.id == rout_point_id)
    result = await session.execute(query)
    rout_point = result.scalars().first()

    if not rout_point:
        raise HTTPException(status_code=404, detail="Rout point not found")

    # Delete related media (images & audio)
    await session.execute(delete(PointMedia).where(PointMedia.rout_point_id == rout_point_id))
    await session.execute(delete(PointsAudio).where(PointsAudio.rout_point_id == rout_point_id))

    # Delete the route point
    await session.delete(rout_point)
    await session.commit()
    return {"message": "Rout point deleted successfully"}