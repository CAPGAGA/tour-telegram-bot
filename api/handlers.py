import hashlib
import os
from datetime import timedelta, datetime
from math import radians, cos, sin, asin, sqrt

import bcrypt
import jwt
from fastapi import Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from settings import SECRET_KEY, ALGORITHM
from db.database import get_session
from db.models import BaseUser


async def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hash_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hash_password.decode('utf-8')

async def create_token(
        data: dict,
        expires_delta: timedelta
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_payment_token(user_id: int, tour_id: int, invoice_id: str):
    """Creates token to sign order"""
    payload = {
        "user_id": user_id,
        "tour_id": tour_id,
        "invoice_id": invoice_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_payment_token(token: str):
    """Decodes token to get user_id and tour_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        tour_id = payload.get("tour_id")
        invoice_id = payload.get('invoice_id')

        return user_id, tour_id, invoice_id
    except jwt.PyJWTError:
        return None, None
    except TypeError:
        return None, None

async def get_auth_token(request: Request):
    """
        Get and check auth token
    """
    return request.cookies.get('auth_token')

async def get_current_creator(request: Request):
    """
        Return base creator info
    """
    token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        is_creator: bool = payload.get('is_creator')

        return user_id, is_creator
    except jwt.PyJWTError:
        return None


async def get_creator_id(
        request: Request,
        session: AsyncSession = Depends(get_session)
):
    """
        Return creator id
    """

    token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        query = select(BaseUser).where(BaseUser.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()

        return user.creator_id
    except jwt.PyJWTError:
        return None

def generate_hashed_filename(filename: str) -> str:
    hash_digest = hashlib.md5(filename.encode()).hexdigest()
    ext = os.path.splitext(filename)[1]
    return f"{hash_digest}{ext}"



async def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles

    return c * r