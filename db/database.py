import logging

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from settings import POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DEBUG

logger = logging.getLogger(__name__)
if DEBUG:
    logger.info('Running with debug mode')
    engine = create_async_engine("sqlite+aiosqlite:///./prod.db")
else:
    logger.info('Running in production mode')
    engine = create_async_engine(f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}")

async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base: DeclarativeMeta = declarative_base()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session