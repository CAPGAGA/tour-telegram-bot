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
from api.utils.handlers import get_auth_token, get_current_creator, get_locale, get_lang_from_session
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

    # functions to output pages
    @app.get('/', response_class=HTMLResponse)
    async def landing(
            request: Request,
            user: Optional[tuple] = Depends(get_current_creator),
            lang: str = Depends(get_locale),
    ):
        return templates.TemplateResponse(
            request=request,
            context={
                "user_id": user[0],
                "is_creator": user[1],
                "lang": lang,

            } if user else {
                "lang": lang,
            },
            name='pages/landing.html'
        )

    @app.get("/for-creators", response_class=HTMLResponse)
    async def for_creators(
            request: Request,
            user: Optional[tuple] = Depends(get_current_creator),
            lang: str = Depends(get_locale),
    ):
        return templates.TemplateResponse(
            request=request,
            context={
                "user_id": user[0],
                "is_creator": user[1],
                "lang": lang,
            } if user else {
                "lang": lang
            },
            name='pages/for-creators.html'
        )

    @app.get('/shop', name='shop')
    async def redirect_to_correct_shop():
        return RedirectResponse(url='/shop/1')

    @app.get('/shop/{page}', response_class=HTMLResponse)
    async def shop(
            request: Request,
            page: int,
            user: Optional[tuple] = Depends(get_current_creator)
    ):
        return templates.TemplateResponse(
            request=request,
            context={"user_id": user[0], "is_creator": user[1]} if user else {},
            name='pages/shop.html'
        )

    @app.get('/tour/{rout_id}')
    async def tour_page(
            request: Request,
            rout_id: int,
            user: Optional[tuple] = Depends(get_current_creator),
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
            context={
                'rout': rout.to_dict(),
                'rout_points': rout_points
            },
            name='pages/tour.html'
        )

    @app.get('/tour/{rout_id}/buy')
    async def tour_purchase_page(
            request: Request,
            rout_id: int,
            user: Optional[tuple] = Depends(get_current_creator),
            session: AsyncSession = Depends(get_session)
    ):
        if not user:
            return RedirectResponse(url="/login?next=/tour/{rout_id}/buy")

        rout = await get_rout_without_points(
            rout_id=rout_id,
            session=session
        )

        return templates.TemplateResponse(
            request=request,
            context={
                "user_id": user[0],
                "tour": rout
            },
            name='pages/checkout.html'
        )

    @app.get('/my-tours', response_class=HTMLResponse)
    async def my_tours_page(
            request: Request,
            user: Optional[tuple] = Depends(get_current_creator),
            session: AsyncSession = Depends(get_session)
    ):
        if not user:
            return RedirectResponse(url='login?next=/my-tours')
        try:
            user_owned_routs = await get_user_routs(user_id=user[0], session=session)
        except:
            user_owned_routs = []

        return templates.TemplateResponse(
            request=request,
            context={
                "user_id": user[0],
                "routs": user_owned_routs
            },
            name='my_tours_page.html'
        )

    @app.get(
        "/test-page", response_class=HTMLResponse
    )
    async def test_page(
            request: Request,
            user: Optional[tuple] = Depends(get_current_creator),
            session: AsyncSession = Depends(get_session)
    ):
        if not user:
            return RedirectResponse(url="/login?next=/test-page")
        return templates.TemplateResponse(
            request=request,
            context={
                "user_id": user[0],
                "is_creator": user[1]
            },
            name='test-pages/test-landing.html'
        )

    @app.get(
        "/payment/success", response_class=HTMLResponse
    )
    async def payment_success(
            request: Request,
    ):
        return templates.TemplateResponse(
            request=request,
            context={},
            name='pages/payments/success.html'
        )


    @app.get(
        "/payment/error", response_class=HTMLResponse
    )
    async def payment_error(
            request: Request,
    ):
        return templates.TemplateResponse(
            request=request,
            context={},
            name='pages/payments/error.html'
        )

    @app.get(
        "/payment/cancel", response_class=HTMLResponse
    )
    async def payment_cancel(
            request: Request,
    ):
        return templates.TemplateResponse(
            request=request,
            context={},
            name='pages/payments/cancel.html'
        )


@app.get('/login', response_class=HTMLResponse)
async def login_page(
        request: Request,
        auth_token: str = Depends(get_auth_token)
):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='pages/login.html'
        )
    return RedirectResponse(url="/tour-admin")

@app.get('/register', response_class=HTMLResponse)
async def register_page(
        request: Request,
        auth_token: str = Depends(get_auth_token)
):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='pages/register.html'
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
    user_id, is_creator = user
    if not is_creator:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = select(BaseUser).where(BaseUser.id == user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        return RedirectResponse(url="/apiV1/auth/logout")


    return templates.TemplateResponse(
        context={
            'username': user.username,
            'creator_id': user.creator_id
        }, request=request, name='tour_admin.html'
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