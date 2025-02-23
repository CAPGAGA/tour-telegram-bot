from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Rout, RoutPoint, AdminRout

async def check_admin_rout_point_access(
        rout_point_id: int,
        admin_id: int,
        session: AsyncSession
):
    """
        Check if user have access (is creator) of rout point (rout
    """
    query = (
            select(Rout)
            .join(RoutPoint, RoutPoint.rout_id == Rout.id)
            .join(AdminRout, AdminRout.rout_id == Rout.id)
            .where(RoutPoint.id == rout_point_id, AdminRout.admin_id == admin_id)
        )
    result = await session.execute(query)
    owned_route = result.scalars().first()

    if not owned_route:
        return False
    return True

async def check_admin_rout_access(
        rout_id: int,
        admin_id: int,
        session: AsyncSession
):
    """
        Check if user have access (is creator) of rout
    """

    query = (
        select(AdminRout).where(
            AdminRout.rout_id == rout_id,
            AdminRout.admin_id == admin_id
        )
    )
    result = await session.execute(query)
    owned_route = result.scalars().first()

    if not owned_route:
        return False
    return True