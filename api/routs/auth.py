from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import BaseUser as User
from db.models import Admin

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class UserCreate(BaseModel):
    user_id: int
    username: str

class UserRegister(BaseModel):

    username: str
    password: str

class UserUpdate(BaseModel):

    username: str
    is_admin: bool


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        orm_mode = True

# Endpoint to create user from telegram
@auth_router.post("/user/register", response_model=UserResponse)
async def create_user(
        user: UserCreate,
        session: AsyncSession = Depends(get_session)
):
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

# Endpoint to create admin from web
@auth_router.get("/admin/register", response_model=UserResponse)
async def create_admin(
        user: UserRegister,
        session: AsyncSession = Depends(get_session)
):
    """Creates base user and admin user with access to creators tools"""
    # Check if user exists
    query = select(User).where(
        User.username == user.username,
        User.is_admin == True
    )
    result = await session.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        # Check if admin exist
        query = select(Admin).where(Admin.username == user.username)
        result = await session.execute(query)
        existing_admin = result.scalars().first()

        if existing_admin:
            # Admin exists return creation error
            raise HTTPException(status_code=400, detail='This admin already exists')
        else:
            # User is admin but does not have admin account create one
            new_admin = Admin(username=user.username, password=user.password)
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            return new_admin
    else:
        pass



@auth_router.get("/user/get-user/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@auth_router.get("/user/get-users", response_model=list[UserResponse])
async def get_all_users(
        session: AsyncSession = Depends(get_session)
):
    query = select(User)
    result = await session.execute(query)
    users = result.scalars().all()
    return users

@auth_router.put("/user/edit-users/{user_id}", response_model=UserResponse)
async def update_user(
        user_id: int,
        user: UserUpdate,
        session: AsyncSession = Depends(get_session)
):
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

@auth_router.delete("/user/delete-users/{user_id}", response_model=dict)
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"message": "User deleted successfully"}



