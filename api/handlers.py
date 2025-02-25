import hashlib
import os
from math import radians, cos, sin, asin, sqrt

import jwt
from fastapi import Request

from api.settings import SECRET_KEY, ALGORITHM

async def get_auth_token(request: Request):
    """
        Get and check auth token
    """
    return request.cookies.get('auth_token')

async def get_current_admin(request: Request):
    """
        Return base admin info
    """
    token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None:
            return None
        return username, user_id
    except jwt.PyJWTError:
        return None


async def get_admin_id(request: Request):
    """
        Return admin id
    """

    token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: int = payload.get("user_id")
        if admin_id is None:
            return None
        return admin_id
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