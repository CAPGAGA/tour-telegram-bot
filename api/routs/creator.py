from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.utils.handlers import get_current_creator
from db.database import get_session
from db.models import CreatorRout, Rout, Order, WithdrawRequest
from db.schemas import RoutSchema
from settings import DEBUG

creator_rout_router = APIRouter(
    prefix="/creator_rout",
    tags=["creator_rout"],
)


class CreatorRoutCreate(BaseModel):

    creator_id: int
    rout_id: int

class CreatorRoutResponse(BaseModel):

    creator_id: int
    routs: list[RoutSchema]

@creator_rout_router.post("/link-rout", response_model=CreatorRoutResponse)
async def link_rout_to_creator(
        creator_rout: CreatorRoutCreate,
        session: AsyncSession = Depends(get_session)
):

    new_admin_rout = CreatorRout(**creator_rout.dict())
    session.add(new_admin_rout)
    await session.commit()
    await session.refresh(new_admin_rout)

    stmt = select(Rout).where(Rout.id == creator_rout.rout_id)
    result = await session.execute(stmt)
    rout = result.scalar_one_or_none()

    return {"creator_id": new_admin_rout.creator_id, "routs": [rout]}

@creator_rout_router.get("/get-creator-rout", response_model=CreatorRoutResponse)
async def get_admin_rout(
        creator_id: int,
        session: AsyncSession = Depends(get_session)
):

    stmt = select(CreatorRout).where(CreatorRout.creator_id == creator_id)
    result = await session.execute(stmt)
    admin_rout = result.scalars().all()

    stmt = select(Rout).where(Rout.id.in_([rout.rout_id for rout in admin_rout]))
    result = await session.execute(stmt)
    routs = result.scalars().all()

    return {"creator_id": creator_id, "routs": [rout for rout  in routs]}

@creator_rout_router.get("/get-creators-stats")
async def get_creators_stats(
    creator=Depends(get_current_creator),
    session: AsyncSession = Depends(get_session),
):
    creator_id, is_creator = creator
    if not is_creator:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Subquery to get creator's route IDs
    creator_rout_subq = select(CreatorRout.rout_id).where(
        CreatorRout.creator_id == creator_id
    ).subquery()

    # Query all paid orders for those routes
    orders_query = select(Order).where(
        Order.rout_id.in_(select(creator_rout_subq.c.rout_id)),
        Order.status == 'paid'
    )

    # Query to get all withdrawals of creator
    withdrawals_query = select(
        WithdrawRequest
    ).where(
        WithdrawRequest.creator_id == creator_id,
        WithdrawRequest.status == 'approved'
    )

    async with session.begin():
        # Get orders
        result = await session.execute(orders_query)
        orders = result.scalars().all()

        w_result = await session.execute(withdrawals_query)
        withdrawals = w_result.scalars().all()

        withdrawaled = sum([float(withdrawal.amount) for withdrawal in withdrawals])

        # Calculate totals from orders
        total_balance = sum([float(order.amount) for order in orders]) - withdrawaled
        total_orders = len(orders)
        unique_clients = len(set(order.user_id for order in orders))

        # Get number of active tours for this creator
        active_tours_query = select(func.count()).select_from(Rout).where(
            Rout.id.in_(select(creator_rout_subq.c.rout_id)),
            Rout.is_displayed == True
        )
        active_tours_result = await session.execute(active_tours_query)
        active_tours = active_tours_result.scalar_one()

    return {
        "total_balance": total_balance,
        "total_orders": total_orders,
        "unique_clients": unique_clients,
        "active_tours": active_tours,
        "withdrawals": withdrawaled
    }


@creator_rout_router.get("/get-sales-per-month")
async def get_sales_per_month(
        creator = Depends(get_current_creator),
        session: AsyncSession = Depends(get_session),
        timescale: str = 'month'  # Default to 'month'
):
    creator_id, is_creator = creator
    if not is_creator:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get the current date
    current_date = datetime.now()

    # Define the start date based on timescale
    if timescale == 'month':
        start_date = current_date.replace(day=1)  # Start from the first day of the current month
    elif timescale == '180days':
        start_date = current_date - timedelta(days=180)
    elif timescale == 'year':
        start_date = current_date.replace(month=1, day=1)  # Start from the first day of the current year
    else:
        raise HTTPException(status_code=400, detail="Invalid timescale")

    if DEBUG:
        # For sqlite
        orders_query = select(
            func.strftime('%Y-%m', Order.created_at).label('month'),  # Group by year-month
            func.sum(Order.amount).label('total_sales')
        ).where(
            Order.rout_id.in_(
                select(CreatorRout.rout_id).where(CreatorRout.creator_id == creator_id)
            ),
            Order.status == 'paid',
            Order.created_at >= start_date  # Filter by start date
        ).group_by('month').order_by('month')
    else:
        # Fetch orders grouped by month within the time range
        orders_query = select(
            func.date_trunc('month', Order.created_at).label('month'),
            func.sum(Order.amount).label('total_sales')
        ).where(
            Order.rout_id.in_(
                select(CreatorRout.rout_id).where(CreatorRout.creator_id == creator_id)
            ),
            Order.status == 'paid',
            Order.created_at >= start_date  # Filter by start date
        ).group_by('month').order_by('month')

    async with session.begin():
        result = await session.execute(orders_query)
        sales_data = result.fetchall()

    months = [sale[0] for sale in sales_data]
    sales = [float(sale[1]) for sale in sales_data]

    return {
        'months': months,
        'sales': sales
    }

