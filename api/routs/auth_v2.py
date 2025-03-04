from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta

from db.database import get_session
from db.models import BaseUser, Creator

from api.handlers import hash_password, create_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    is_creator: bool
    email: Optional[str] = None

@auth_router.post("/register-user")
async def register_user(
    user_data: UserRegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check if user exists
    query = select(BaseUser).where(BaseUser.username == user_data.username)
    result = await session.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_creator = None
    if user_data.is_creator:
        if not user_data.email:
            raise HTTPException(status_code=403, detail="Email required for creator")

        query = select(Creator).where(Creator.email == user_data.email)
        result = await session.execute(query)
        existing_creator = result.scalars().first()

        if existing_creator:
            raise HTTPException(status_code=400, detail="Creator already exists")

        new_creator = Creator(email=user_data.email, is_active=True)
        session.add(new_creator)
        await session.commit()
        await session.refresh(new_creator)


    # Hash the password
    hashed_password = await hash_password(user_data.password)

    # Create new user
    if user_data.is_creator and new_creator:
        new_user = BaseUser(
            username=user_data.username,
            password=hashed_password,
            is_creator=True,
            is_admin=False,
            creator_id=new_creator.id
        )
    else:
        new_user = BaseUser(
            username=user_data.username,
            password=hashed_password,
            is_admin=False
        )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Generate token
    token = await create_token(
        {
            "user_id": new_user.id,
            "is_creator": user_data.is_creator
        }, timedelta(days=30)
    )

    return {"message": "User registered successfully", "token": token}


class TelegramRegisterRequest(BaseModel):
    user_id: int
    username: str

@auth_router.post("/register-telegram")
async def register_telegram_user(
    user_data: TelegramRegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check if user exists
    query = select(BaseUser).where(BaseUser.user_id == user_data.user_id)
    result = await session.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        return {"message": "User already registered", "user_id": existing_user.id}

    # Register new Telegram user (No password required)
    new_user = BaseUser(
        user_id=user_data.user_id,
        username=user_data.username,
        is_admin=False
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return {"message": "Telegram user registered successfully", "user_id": new_user.id}

class LoginRequest(BaseModel):
    username: str
    password: str

@auth_router.post("/login")
async def login_user(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check if user exists in BaseUser table
    query = select(BaseUser).where(BaseUser.username == login_data.username)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password using bcrypt
    if not bcrypt.checkpw(login_data.password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT Token
    token = await create_token(
        # Important to switch id between admin and user
        {
            "user_id": user.id,
            "is_creator": user.is_creator
        },
        timedelta(days=30)
    )

    return {"message": "Login successful", "token": token, "is_creator": user.is_creator}

class TelegramLoginRequest(BaseModel):
    user_id: int

@auth_router.post("/login-telegram")
async def login_telegram_user(
    login_data: TelegramLoginRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check if user exists in BaseUser table
    query = select(BaseUser).where(BaseUser.user_id == login_data.user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please register first.")

    # Generate JWT Token
    token_data = {
        "user_id": user.id,
        "is_creator": user.is_creator  # Admin status is dynamically assigned
    }

    token = await create_token({"user_id": login_data.user_id, "is_creator": user.is_creator}, timedelta(days=30))

    return {"message": "Login successful", "token": token, "is_creator": user.is_creator}


@auth_router.get('/logout')
async def logout_admin(response: Response):
    response.delete_cookie("auth_token")
    return