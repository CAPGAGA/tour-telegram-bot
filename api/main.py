import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.handlers import get_auth_token, get_current_creator
from api.routs.creator import creator_rout_router
from api.routs.auth_v2 import auth_router
from api.routs.media import point_media_router
from api.routs.orders import order_router
from api.routs.routs import rout_router
from api.routs.rout_points import rout_points_router
from api.routs.users import user_routs_router

from db.database import Base, engine, get_session
from db.models import Creator, BaseUser

from settings import DEBUG

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
     Api startup function
    """
    if DEBUG:
        logger.info('Running with debug mode')
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info('All table are created! Database is up to date!')
        except Exception as e:
            logger.error(f'Error while starting api: {e}')
    else:
        logger.info('Running in production mode')
    yield


app = FastAPI(lifespan=lifespan)
# mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount('/media', StaticFiles(directory='web/media'), name='media')
templates = Jinja2Templates(directory="web/templates")


# base routs of api
app.include_router(creator_rout_router, prefix='/apiV1')
app.include_router(auth_router, prefix='/apiV1')
app.include_router(rout_router, prefix='/apiV1')
app.include_router(rout_points_router, prefix='/apiV1')
app.include_router(user_routs_router, prefix='/apiV1')
app.include_router(point_media_router, prefix='/apiV1')
app.include_router(order_router, prefix='/apiV1')

# functions to output pages
@app.get('/', response_class=HTMLResponse)
async def landing(
        request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name='landing.html'
    )

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request, auth_token: str = Depends(get_auth_token)):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='login.html'
        )
    return RedirectResponse(url="/tour-admin")

@app.get('/register', response_class=HTMLResponse)
async def login_page(
        request: Request,
        auth_token: str = Depends(get_auth_token)
):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='register.html'
        )
    return RedirectResponse(url="/tour-admin")

@app.get('/tour-admin', response_class=HTMLResponse)
async def tour_admin(
        request: Request,
        user: str = Depends(get_current_creator),
        session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse(url="/login")
    print(user)
    user_id, is_creator = user
    if not is_creator:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = select(BaseUser).where(BaseUser.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    return templates.TemplateResponse(
        context={
            'username': user.username,
            'creator_id': user.creator_id
        }, request=request, name='tour_admin.html'
    )