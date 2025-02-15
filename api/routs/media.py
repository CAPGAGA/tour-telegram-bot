from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
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