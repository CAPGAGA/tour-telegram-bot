import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routs.auth import auth_router
from api.routs.routs import rout_router
from api.routs.rout_points import rout_points_router
from api.routs.user_routs import user_routs_router

from db.database import Base, engine

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
     Api startup function
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info('All table are created! Database is up to date!')
    except Exception as e:
        logger.error(f'Error while starting api: {e}')

    yield


app = FastAPI(lifespan=lifespan)

# base routs of api
app.include_router(auth_router, prefix='/apiV1')
app.include_router(rout_router, prefix='/apiV1')
app.include_router(rout_points_router, prefix='/apiV1')
app.include_router(user_routs_router, prefix='/apiV1')