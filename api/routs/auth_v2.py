from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta

from db.database import get_session
from db.models import BaseUser, Admin

from api.handlers import hash_password, create_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class UserRegisterRequest(BaseModel):
    username: str
    password: str

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

    # Hash the password
    hashed_password = await hash_password(user_data.password)

    # Create new user
    new_user = BaseUser(
        username=user_data.username,
        password=hashed_password,
        is_admin=False
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Generate token
    token = await create_token({"user_id": new_user.id, "is_admin": False}, timedelta(days=30))

    return {"message": "User registered successfully", "token": token}

class AdminRegisterRequest(BaseModel):
    username: str
    password: str

@auth_router.post("/register-admin")
async def register_admin(
    admin_data: AdminRegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    # Check if admin exists in Admin table
    query_admin = select(Admin).where(Admin.username == admin_data.username)
    result_admin = await session.execute(query_admin)
    existing_admin = result_admin.scalars().first()

    # Check if admin exists in BaseUser table
    query_user = select(BaseUser).where(BaseUser.username == admin_data.username)
    result_user = await session.execute(query_user)
    existing_user = result_user.scalars().first()

    if existing_admin or existing_user:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Hash the password
    hashed_password = await hash_password(admin_data.password)

    # Create new admin entry
    new_admin = Admin(
        username=admin_data.username,
        password=hashed_password,
        is_active=True
    )
    session.add(new_admin)
    await session.commit()
    await session.refresh(new_admin)

    # Create a corresponding BaseUser entry with is_admin=True
    new_user = BaseUser(
        username=admin_data.username,
        password=hashed_password,
        is_admin=True,
        admin_id=new_admin.id
    )


    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Generate JWT token
    token = await create_token({"user_id": new_user.id, "is_admin": True}, timedelta(days=30))

    return {"message": "Admin registered successfully", "token": token}

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
            "user_id": user.admin_id if user.is_admin else user.id,
            "is_admin": user.is_admin
        },
        timedelta(days=30)
    )

    return {"message": "Login successful", "token": token, "is_admin": user.is_admin}

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
        "is_admin": user.is_admin  # Admin status is dynamically assigned
    }

    token = await create_token({"user_id": login_data.user_id, "is_admin": user.is_admin}, timedelta(days=30))

    return {"message": "Login successful", "token": token, "is_admin": user.is_admin}


@auth_router.get('/logout')
async def logout_admin(response: Response):
    response.delete_cookie("auth_token")
    return