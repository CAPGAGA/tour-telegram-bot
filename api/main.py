import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_babel import BabelMiddleware, BabelConfigs

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from api.cron.update_currency_rates import fetch_and_store_currency_rates, ensure_currency_rates
from api.middleware.user import UserMiddleware
from api.utils.handlers import get_auth_token, get_lang_from_session
from api.routs.creator import creator_rout_router
from api.routs.auth_v2 import auth_router
from api.routs.geo import geocode_router
from api.routs.media import point_media_router
from api.routs.orders import order_router
from api.routs.promo import promo_router
from api.routs.routs import rout_router, get_rout as get_rout_without_points
from api.routs.rout_points import rout_points_router, get_rout as get_rout_with_points
from api.routs.search import search_router
from api.routs.user import user_router
from api.routs.user_routs import user_routs_router, get_user_routs

from api.sitemap import sitemap

from db.database import Base, engine, get_session
from db.models import BaseUser, Rout

from settings import DEBUG, SECRET_KEY, HEADLESS_MODE

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

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
    await ensure_currency_rates()

    scheduler.start()
    # update currencies every day at 6 AM UTC
    scheduler.add_job(
        fetch_and_store_currency_rates, CronTrigger(hour=6, minute=0)
    )
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.add_middleware(UserMiddleware)

# mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount('/media', StaticFiles(directory='web/media'), name='media')
templates = Jinja2Templates(directory="web/templates")


# Babel config
babel_configs = BabelConfigs(
    ROOT_DIR=Path(__file__).parent,
    BABEL_DEFAULT_LOCALE="en",
    BABEL_TRANSLATION_DIRECTORY=os.path.join(Path(__file__).parent.parent, "lang"),
)

# base routs of api
app.include_router(creator_rout_router, prefix='/apiV1')
app.include_router(auth_router, prefix='/apiV1')
app.include_router(rout_router, prefix='/apiV1')
app.include_router(rout_points_router, prefix='/apiV1')
app.include_router(user_routs_router, prefix='/apiV1')
app.include_router(point_media_router, prefix='/apiV1')
app.include_router(order_router, prefix='/apiV1')
app.include_router(search_router, prefix='/apiV1')
app.include_router(user_router, prefix='/apiV1')
app.include_router(geocode_router, prefix='/apiV1')
app.include_router(promo_router, prefix='/apiV1')

if not HEADLESS_MODE:
    # util urls
    app.mount('/sitemap.xml', sitemap)

    @app.get('/', response_class=HTMLResponse)
    async def landing(
            request: Request,
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/landing.html',
            context={**request.state.user}
        )

    @app.get("/for-creators", response_class=HTMLResponse)
    async def for_creators(
            request: Request,
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/for-creators.html',
            context={**request.state.user}
        )

    @app.get('/shop', name='shop')
    async def redirect_to_correct_shop():
        return RedirectResponse(url='/shop/1')

    @app.get('/shop/{page}', response_class=HTMLResponse)
    async def shop(
            request: Request,
            page: int,
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/shop.html',
            context={**request.state.user, "page": page}
        )

    @app.get('/tour/{rout_id}')
    async def tour_page(
        request: Request,
        rout_id: int,
        session: AsyncSession = Depends(get_session)
    ):
        query = select(Rout).where(Rout.id == rout_id)
        result = await session.execute(query)
        rout = result.scalars().first()
        if not rout:
            raise HTTPException(status_code=404, detail="Rout not found")

        rout_points = await get_rout_with_points(rout_id, session)
        
        return templates.TemplateResponse(
            request=request,
            name='pages/tour.html',
            context={
                **request.state.user,
                'rout': rout.to_dict(),
                'rout_points': rout_points
            }
        )

    @app.get('/tour/{rout_id}/buy')
    async def tour_purchase_page(
        request: Request,
        rout_id: int,
        session: AsyncSession = Depends(get_session)
    ):
        if not request.state.user:
            return RedirectResponse(url=f"/login?next=/tour/{rout_id}/buy")

        rout = await get_rout_without_points(rout_id=rout_id, session=session)
        return templates.TemplateResponse(
            request=request,
            name='pages/checkout.html',
            context={
                **request.state.user,
                "tour": rout
            }
        )

    @app.get('/my-tours', response_class=HTMLResponse)
    async def my_tours_page(
        request: Request,
        session: AsyncSession = Depends(get_session)
    ):
        if not request.state.user:
            return RedirectResponse(url='login?next=/my-tours')
        
        try:
            user_owned_routs = await get_user_routs(
                user_id=request.state.user['user']['id'],
                session=session
            )
        except:
            user_owned_routs = []

        return templates.TemplateResponse(
            request=request,
            name='pages/my_tours.html',
            context={
                **request.state.user,
                "routs": user_owned_routs
            }
        )

    @app.get("/test-page", response_class=HTMLResponse)
    async def test_page(
            request: Request,
    ):
        if not request.state.user:
            return RedirectResponse(url="/login?next=/test-page")
        return templates.TemplateResponse(
            request=request,
            name='test-pages/test-landing.html',
            context={
                **request.state.user,
            }
        )

    @app.get("/payment/success", response_class=HTMLResponse)
    async def payment_success(
            request: Request
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/payments/success.html',
            context={
                **request.state.user,
            }
        )

    @app.get("/payment/error", response_class=HTMLResponse)
    async def payment_error(
            request: Request
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/payments/error.html',
            context={
                **request.state.user,
            }
        )

    @app.get("/payment/cancel", response_class=HTMLResponse)
    async def payment_cancel(
            request: Request
    ):
        return templates.TemplateResponse(
            request=request,
            name='pages/payments/cancel.html',
            context={
                **request.state.user,
            }
        )

@app.get('/login', response_class=HTMLResponse)
async def login_page(
    request: Request,
):
    if not request.state.user:
        return templates.TemplateResponse(
            request=request,
            name='pages/login.html',
            context={
                **request.state.user,
            }
        )
    return RedirectResponse(url="/tour-admin")

@app.get('/register', response_class=HTMLResponse)
async def register_page(
    request: Request,
    auth_token: str = Depends(get_auth_token)
):
    if not auth_token:
        return templates.TemplateResponse(
            request=request,
            name='pages/register.html',
            context={
                **request.state.user,
            }
        )
    return RedirectResponse(url="/tour-admin")

@app.get('/tour-admin', response_class=HTMLResponse)
async def tour_admin(
    request: Request,

    session: AsyncSession = Depends(get_session)
):
    if not request.state.user:
        return RedirectResponse(url="/login")
    if not request.state.user['user'].get('is_creator'):
        raise HTTPException(status_code=403, detail="Forbidden")

    query = select(BaseUser).where(BaseUser.id == request.state.user['user']['id'])
    result = await session.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        return RedirectResponse(url="/apiV1/auth/logout")

    return templates.TemplateResponse(
        request=request,
        name='tour_admin.html',
        context={
            **request.state.user,
            'username': db_user.username,
            'creator_id': db_user.creator_id
        }
    )

# middleware
app.add_middleware(
    BabelMiddleware,
    babel_configs=babel_configs,
    jinja2_templates=templates,
    locale_selector=get_lang_from_session,
)

# IMPORTANT! MUST BE ON LAST LINE
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)