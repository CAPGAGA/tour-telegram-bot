import os
from datetime import timedelta, datetime

import bcrypt
from fastapi import APIRouter, HTTPException, Depends, Response
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from api.handlers import create_token, hash_password
from api.settings import SECRET_KEY, ALGORITHM, TOKEN_EXPIRATION_MINUTES

from db.database import get_session
from db.models import Admin

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

class AdminCreate(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    token: str
    expires_in: timedelta

    class Config:
        orm_mode = True


@admin_router.post("/register", response_model=AdminResponse)
async def create_admin(admin: AdminCreate, session: AsyncSession = Depends(get_session)):
    """
        Endpoint to register admin. Create active admin only for first registration
        later admins must be activated from crm panel
    """
    stmt = select(Admin)
    admin_db = await session.execute(stmt)
    admin_db = admin_db.scalars().first()
    if admin_db:
        stmt = select(Admin).where(Admin.username == admin.username)
        admin_db = await session.execute(stmt)
        admin_db = admin_db.scalars().first()
        if admin_db:
            raise HTTPException(status_code=403, detail="This username already exists")
        new_admin = Admin(username=admin.username, password=await hash_password(admin.password), is_active=True)
        session.add(new_admin)
        await session.commit()
        raise HTTPException(status_code=400, detail="Admin already exists. Contact an administrator for permission.")
    new_admin = Admin(username=admin.username, password=await hash_password(admin.password), is_active=True)
    session.add(new_admin)
    await session.commit()
    await session.refresh(new_admin)
    expires_delta = timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
    token = await create_token({"sub": new_admin.username, "user_id": new_admin.id}, expires_delta)
    return {'token': token, 'expires_in': expires_delta}

@admin_router.post('/crm-login', response_model=AdminResponse)
async def login_admin(admin: AdminCreate, session: AsyncSession = Depends(get_session)):
    """
        Endpoint to login admin.
    """

    stmt = select(Admin).where(Admin.username == admin.username)
    result = await session.execute(stmt)
    admin_db = result.scalars().first()

    if not admin_db:
        raise HTTPException(status_code=404, detail="Username not found")

    if not admin_db.is_active:
        raise HTTPException(status_code=400, detail="Username is not active. Contact an administrator for permission")

    if not bcrypt.checkpw(hashed_password=admin_db.password.encode('utf-8'), password=admin.password.encode('utf-8')):
        raise HTTPException(status_code=403, detail="Wrong password")

    expires_delta = timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
    token = await create_token({"sub": admin_db.username, "user_id": admin_db.id}, expires_delta)
    return {'token': token, 'expires_in': expires_delta}


@admin_router.get('/logout')
async def logout_admin(response: Response):
    response.delete_cookie("auth_token")
    return