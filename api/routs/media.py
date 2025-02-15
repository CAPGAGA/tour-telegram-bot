from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, delete
from  sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import PointMedia, PointsAudio


point_media_router = APIRouter(
    prefix="/point-media",
    tags=["point-media"],
)

class MediaCreate(BaseModel):

    rout_point_id: int


class AudioCreate(BaseModel):

    rout_point_id: int

@point_media_router.post("/add-image")
async def add_image(
    rout_point_id: int,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        new_image = PointMedia(rout_point_id=rout_point_id, media_name=image.filename)
        session.add(new_image)
        await session.commit()
        return {"message": "Image uploaded successfully", "id": new_image.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@point_media_router.post("/add-audio")
async def add_audio(
    rout_point_id: int,
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        new_audio = PointsAudio(rout_point_id=rout_point_id, audio_name=audio.filename)
        session.add(new_audio)
        await session.commit()
        return {"message": "Audio uploaded successfully", "id": new_audio.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@point_media_router.get("/get-images/{rout_point_id}")
async def get_images(rout_point_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PointMedia).where(PointMedia.rout_point_id == rout_point_id))
    images = result.scalars().all()
    return images

@point_media_router.get("/get-audios/{rout_point_id}")
async def get_audios(rout_point_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PointsAudio).where(PointsAudio.rout_point_id == rout_point_id))
    audios = result.scalars().all()
    return audios

@point_media_router.delete("/delete-image/{image_id}")
async def delete_image(image_id: int, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(PointMedia).where(PointMedia.id == image_id))
    await session.commit()
    return {"message": "Image deleted successfully"}

@point_media_router.delete("/delete-audio/{audio_id}")
async def delete_audio(audio_id: int, session: AsyncSession = Depends(get_session)):
    await session.execute(delete(PointsAudio).where(PointsAudio.id == audio_id))
    await session.commit()
    return {"message": "Audio deleted successfully"}