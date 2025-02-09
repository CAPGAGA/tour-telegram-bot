import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    id: int
    username: str

async def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hash_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hash_password.decode('utf-8')

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
    return new_admin

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

    password = await hash_password(admin.password)

    if not bcrypt.checkpw(admin.password.encode('utf-8'), password.encode('utf-8')):
        raise HTTPException(status_code=403, detail="Wrong password")

    return admin_db
