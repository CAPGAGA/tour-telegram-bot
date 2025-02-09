import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from api.handlers import get_auth_token
from api.routs.auth import auth_router
from api.routs.crm_auth import admin_router
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
# mount static files
app.mount("/static", StaticFiles(directory="crm/static"), name="static")
templates = Jinja2Templates(directory="crm/templates")


# base routs of api
app.include_router(admin_router, prefix='/apiV1')
app.include_router(auth_router, prefix='/apiV1')
app.include_router(rout_router, prefix='/apiV1')
app.include_router(rout_points_router, prefix='/apiV1')
app.include_router(user_routs_router, prefix='/apiV1')

# crm renders
@app.get('/', response_class=HTMLResponse)
async def index(auth_token: str = Depends(get_auth_token)):
    if not auth_token:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/crm")

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request, auth_token: str = Depends(get_auth_token)):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='login.html'
        )

@app.get('/register', response_class=HTMLResponse)
async def login_page(request: Request, auth_token: str = Depends(get_auth_token)):
    if not auth_token:
        return templates.TemplateResponse(
            request=request, name='register.html'
        )