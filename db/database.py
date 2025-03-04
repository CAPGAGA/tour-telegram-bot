from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///./prod.db")

async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


Base: DeclarativeMeta = declarative_base()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session