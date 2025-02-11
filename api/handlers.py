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



