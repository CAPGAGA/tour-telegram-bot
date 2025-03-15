from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import BaseUser, UserRout, Rout

user_routs_router = APIRouter(
    prefix="/user_routs",
    tags=["user_routs"],
)

class UserRoutCreate(BaseModel):

    user_id: int
    rout_id: int

class UserRoutResponse(BaseModel):

    id: int
    user_id: int
    rout_id: int

class DetailedUserRoutResponse(BaseModel):

    id: int
    user_id: int
    rout_id: int
    rout_name: str
    rout_description: str
    base_price: float
    image: Optional[str] = None
    is_displayed: bool


@user_routs_router.post("/create", response_model=UserRoutResponse)
async def create_user_rout(
        user_rout: UserRoutCreate,
        session: AsyncSession = Depends(get_session)
):
    new_user_rout = UserRout(**user_rout.dict())
    session.add(new_user_rout)
    await session.commit()
    await session.refresh(new_user_rout)
    return new_user_rout

@user_routs_router.get("/get-user-rout", response_model=list[DetailedUserRoutResponse])
async def get_user_routs(
        user_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = (
        select(UserRout, Rout)
        .join(Rout, Rout.id == UserRout.rout_id)
        .where(UserRout.user_id == user_id)
    )

    result = await session.execute(query)
    user_routs = result.all()

    if not user_routs:
        raise HTTPException(status_code=404, detail="User has no routes")
    # Format response
    response = []
    for user_rout in user_routs:
        response.append(
            DetailedUserRoutResponse(
                id=user_rout.UserRout.id,
                user_id=user_rout.UserRout.user_id,
                rout_id=user_rout.UserRout.rout_id,
                rout_name=user_rout.Rout.rout_name,
                rout_description=user_rout.Rout.rout_description,
                base_price=user_rout.Rout.base_price,
                image=user_rout.Rout.image,
                is_displayed=user_rout.Rout.is_displayed
            )
        )
    return response

@user_routs_router.get("/check-user-rout", response_model=dict)
async def check_user_rout(
        user_id: int,
        rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(UserRout).where(UserRout.user_id == user_id, UserRout.rout_id == rout_id)
    result = await session.execute(query)
    user_rout = result.scalars().first()
    if not user_rout:
        raise HTTPException(status_code=404, detail="User have no rout")
    return {"message": "User have rout"}


@user_routs_router.delete("/delete-user-rout", response_model=dict)
async def delete_user_rout(
        user_rout_id: int,
        session: AsyncSession = Depends(get_session)
):
    query = select(UserRout).where(UserRout.id == user_rout_id)
    result = await session.execute(query)
    if not result:
        raise HTTPException(status_code=404, detail="User rout not found")
    user_rout = result.scalars().first()
    await session.delete(user_rout)
    await session.commit()
    return {"message": "User rout deleted successfully"}