from fastapi import Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from settings import SECRET_KEY, ALGORITHM

from db.database import get_session
from db.models import BaseUser


class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self,
            request: Request,
            call_next,
    ):
        request.state.user = None
        token = request.cookies.get("auth_token")

        if token:
            try:
                payload = jwt.decode(
                    token,
                    SECRET_KEY,
                    algorithms=[ALGORITHM]
                )
                async for session in get_session():
                    async with session.begin():
                        result = await session.execute(
                            select(
                                BaseUser
                            ).where(
                                BaseUser.id == payload.get("user_id")
                            )
                        )
                user = result.scalars().first()

                request.state.user = {
                    "user": {
                        "id": payload.get("user_id"),
                        "is_creator": payload.get("is_creator", False),
                        "username": user.username if user else None,
                        "email": user.email if user else None,

                    }
                }
            except jwt.PyJWTError:
                pass

        request.state.lang = request.session.get('lang', 'en')
        response = await call_next(request)
        return response
