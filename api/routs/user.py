from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

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
    return {
        "message": "Language set successfully",
        "lang": lang
    }