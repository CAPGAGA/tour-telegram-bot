from sqlalchemy import update

from fastapi import APIRouter, Request

from api.utils.handlers import get_current_user

from db.models import BaseUser
from db.database import get_session

user_router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@user_router.post("/set-language/{lang}")
async def set_user_language(
        lang: str,
        request: Request
):
    if lang in {"en", "ru"}:
        request.session['language'] = lang

    user = await get_current_user(request)

    if user:
        # update user lang in database
        async for session in get_session():
            async with session.begin():
                await session.execute(
                    update(BaseUser)
                    .where(BaseUser.id == user)
                    .values(lang=lang)
                )
                await session.commit()


    return {
        "message": "Language set successfully",
        "lang": lang
    }

@user_router.post('/set-language-external')
async def set_user_language_external(
        user_id: int,
        lang: str
):
    async for session in get_session():
        async with session.begin():
            await session.execute(
                update(BaseUser)
                .where(BaseUser.id == user_id)
                .values(lang=lang)
            )
            await session.commit()

    return {
        "message": "Language set successfully",
        "lang": lang
    }