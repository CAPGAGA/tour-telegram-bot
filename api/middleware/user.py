from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from settings import SECRET_KEY, ALGORITHM


class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        token = request.cookies.get("auth_token")

        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                request.state.user = {
                    "id": payload.get("user_id"),
                    "is_creator": payload.get("is_creator", False)
                }
            except jwt.PyJWTError:
                pass

        response = await call_next(request)
        return response
