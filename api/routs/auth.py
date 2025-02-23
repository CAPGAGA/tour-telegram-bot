from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import BaseUser as User

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class UserCreate(BaseModel):
    user_id: int
    username: str

class UserUpdate(BaseModel):

    username: str
    is_admin: bool


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        orm_mode = True


@auth_router.post("/register", response_model=UserResponse)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    # check if user exists:
    query = select(User).where(User.user_id == user.user_id)
    result = await session.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        return existing_user

    new_user = User(**user.dict())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@auth_router.get("/get-user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@auth_router.get("/get-users", response_model=list[UserResponse])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    query = select(User)
    result = await session.execute(query)
    users = result.scalars().all()
    return users

@auth_router.put("/edit-users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, session: AsyncSession = Depends(get_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    session_user = result.scalars().first()
    if not session_user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict().items():
        setattr(session_user, key, value)
    session.add(session_user)
    await session.commit()
    await session.refresh(session_user)
    return session_user

@auth_router.delete("/delete-users/{user_id}", response_model=dict)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"message": "User deleted successfully"}

