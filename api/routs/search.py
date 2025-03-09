from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from db.database import get_session
from db.models import Rout


search_router = APIRouter(
    prefix="/search",
    tags=["search"],
)

class SearchRout(BaseModel):

    id: int
    rout_name: str
    base_price: float
    rout_description: str
    image: Optional[str] = None


class SearchResponse(BaseModel):

    routs: list[SearchRout]



@search_router.get('/get-routs', response_model=list)
async def get_routs_by_filter(
        search: str = Query(None, title="Tour's name"),
        city: str = Query(None, title="Tour's city"),
        country: str = Query(None, title="Tour's country"),
        max_price: float = Query(None, title="Tour's max price"),
        min_rating: int = Query(None, title="Tour's min rating"),
        page: int = Query(1, title="Page number", ge=1),
        limit: int = Query(10, title="Number of items per page", ge=1),
        session: AsyncSession = Depends(get_session),

):
    """
    Fetches tours from database with provided filters
    """

    query = select(Rout).where(Rout.is_displayed == True)

    if search:
        query = query.where(Rout.rout_name.ilike(f"%{search}%"))

    if city:
        query = query.where(Rout.city.ilike(f"%{city}%"))

    if country:
        query = query.where(Rout.country.ilike(f"%{country}%"))

    if max_price:
        query = query.where(Rout.base_price <= max_price)

    if min_rating:
        query = query.where(Rout.rating >= min_rating)

    query = query.limit(limit).offset((page - 1) * limit)

    result = await session.execute(query)
    routs = result.scalars().all()

    return [rout.to_dict() for rout in routs]