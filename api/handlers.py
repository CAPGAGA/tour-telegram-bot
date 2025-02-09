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
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None


