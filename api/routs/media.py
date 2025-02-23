import os

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, delete
from  sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import PointMedia, PointsAudio
from api.handlers import generate_hashed_filename, get_admin_id
from api.access_checkers import check_admin_rout_point_access



point_media_router = APIRouter(
    prefix="/point-media",
    tags=["point-media"],
)

UPLOAD_IMAGE_DIR = "crm/media/images"
UPLOAD_AUDIO_DIR = "crm/media/audio"

os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)
os.makedirs(UPLOAD_AUDIO_DIR, exist_ok=True)

class MediaCreate(BaseModel):

    rout_point_id: int


class AudioCreate(BaseModel):

    rout_point_id: int

@point_media_router.post("/add-image")
async def add_image(
        rout_point_id: int,
        image: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        admin_id: int = Depends(get_admin_id)
):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not image:
        raise HTTPException(status_code=400, detail="No image provided")

    have_access = await check_admin_rout_point_access(rout_point_id, admin_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    try:
        hashed_filename = generate_hashed_filename(image.filename)
        file_path = os.path.join(UPLOAD_IMAGE_DIR, hashed_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())

        new_image = PointMedia(rout_point_id=rout_point_id, media_name=hashed_filename)
        session.add(new_image)
        await session.commit()
        return {"message": "Image uploaded successfully", "id": new_image.id, "file": f'media/images/{hashed_filename}'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@point_media_router.post("/add-audio")
async def add_audio(
        rout_point_id: int,
        audio: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        admin_id: int = Depends(get_admin_id)
):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not audio:
        raise HTTPException(status_code=400, detail="No audio provided")

    have_access = await check_admin_rout_point_access(rout_point_id, admin_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    try:
        hashed_filename = generate_hashed_filename(audio.filename)
        file_path = os.path.join(UPLOAD_AUDIO_DIR, hashed_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())

        new_audio = PointsAudio(rout_point_id=rout_point_id, audio_name=hashed_filename)
        session.add(new_audio)
        await session.commit()
        return {"message": "Audio uploaded successfully", "id": new_audio.id, "file": f'media/audio/{hashed_filename}'}
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

@point_media_router.delete("/delete-image/{rout_point_id}/{file_name}")
async def delete_image(
        rout_point_id: int,
        file_name: str,
        session: AsyncSession = Depends(get_session),
        admin_id: int = Depends(get_admin_id)
):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_point_access(rout_point_id, admin_id, session)

    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")


    await session.execute(delete(PointMedia).where(PointMedia.media_name == file_name))
    await session.commit()
    return {"message": "Image deleted successfully"}

@point_media_router.delete("/delete-audio/{rout_point_id}/{file_name}")
async def delete_audio(
        rout_point_id: int,
        file_name: str,
        session: AsyncSession = Depends(get_session),
        admin_id: int = Depends(get_admin_id)
):
    if not admin_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    have_access = await check_admin_rout_point_access(rout_point_id, admin_id, session)
    if not have_access:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this route")

    await session.execute(delete(PointsAudio).where(PointsAudio.audio_name == file_name))
    await session.commit()
    return {"message": "Audio deleted successfully"}