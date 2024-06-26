import json

from fastapi import FastAPI, File, UploadFile, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Union, Annotated
from handlers import generate_hash_key, validate_key, validate_user_key

import asyncio

from sqlalchemy.sql import select, update, delete
from datetime import datetime
from settings import DEBUG, MEDIA_DIR

from sql import database, users, routes, rout_points, admins, keys

import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

app = FastAPI()

# connecting to database on startup
@app.on_event("startup")
async def startup():
    await database.connect()
    print('database connected')

# exiting database on shutdown
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    print('database disconnected')

# API ENDPOINTS
# fires up at pressing [start] button in telegram bot
@app.post("/register-user/{username}/")
async def create_user(username: str, chat_id:int) -> dict:
    query = select(users).where(users.columns.username == username)
    user_record = await database.fetch_one(query)
    if user_record:
        if user_record.access_granted:
            # TODO отправка ответа, что пользователь известен, но не имеет подписку
            return {'user':'with access'}
        else:
            # TODO отправка ответа, что пользователь уже известен боту и имеет подписку
            return {'user':'without access'}
    else:
        hash_key = await generate_hash_key(int(chat_id))
        query_user = users.insert().values(username = username if username else None,
                                      chat_id =  chat_id if chat_id else None,
                                      access_granted = False,
                                      registration_date = datetime.now(),
                                      current_rout = 0,
                                      current_rout_point = 0,
                                      user_reg_hash = hash_key)
        await database.execute(query_user)

        query_key = keys.insert().values(
            key=hash_key,
            used=False
        )
        await database.execute(query_key)

        last_record_id = await database.execute(query)
        return {"id": last_record_id}

@app.post('/admins/')
async def create_admin(chat_id: int, username: str) -> dict:
    query = admins.insert().values(
        chat_id = chat_id,
        username = username
    )
    new_admin = await database.execute(query=query)
    return {"id": new_admin}

@app.get('/admins/')
async def get_admins():
    query = select(admins)
    admins_list = await database.fetch_all(query)
    return admins_list

@app.get('/get-user/{username}/')
async def get_user(username: str) -> dict:
    query = select(users).where(users.columns.username == username)
    user_record = await database.fetch_one(query)
    if user_record:
        return user_record
    return None

@app.post('/set-user-rout/{username}/{rout_id}')
async def set_rout(username: str, rout_id: int) -> dict:
    query = update(users).values(current_rout=rout_id).where(users.columns.username == username)
    await database.execute(query)
    return {'rout updated': rout_id}

@app.post('/set-user-rout-point/{username}/{rout_point_id}')
async def set_rout_point(username: str, rout_point_id: int) -> dict:
    query = update(users).values(current_rout_point=rout_point_id).where(users.columns.username == username)
    await database.execute(query)
    return {'rout point updated': rout_point_id}

@app.get('/check_access/{username}/')
async def check_access(username: str) -> dict:
    query = select(users).where(users.columns.username == username)
    user_record = await database.fetch_one(query)
    if user_record.access_granted:
        return {'user': 'with access'}
    else:
        return {'user': 'without access'}

@app.post('/test_access/{username}/')
async def grant_test_access(username: str) -> dict:
    if DEBUG:
        query = update(users).values(access_granted = True).where(users.columns.username == username)
        await database.execute(query)
        return {'user': 'access granted'}
    else:
        return {'debug': 'isoff'}

# get all routs
@app.get("/routs/")
async def get_routs():
    query = routes.select()
    return await database.fetch_all(query)

@app.post("/routs/{rout_name}")
async def add_rout(rout_name: str) -> dict:
    query = routes.insert().values(rout_name=rout_name)
    await database.execute(query)
    return {'rout':'added'}

@app.delete("/routs/{rout_id}")
async def delete_rout(rout_id: int) -> dict:
    query = delete(routes).where(routes.columns.id == rout_id)
    await database.execute(query)
    point_query = delete(rout_points).where(rout_points.columns.rout_id == rout_id)
    await database.execute(point_query)
    return {'deleted': rout_id}

@app.put("/routs/{rout_id}/{rout_name}")
async def edit_rout(rout_id: int, rout_name: str) -> dict:
    query = update(routes).values(rout_name = rout_name).where(routes.columns.id == rout_id)
    await database.execute(query)
    return {'updated': rout_name}

# get all routs points in selected rout
@app.get("/routs/{rout_id}")
async def get_routs_points(rout_id: int) -> list:
    query = select(rout_points).where(rout_points.columns.rout_id == rout_id)
    return await database.fetch_all(query)

# class CustomUploadFile(UploadFile):
#
#     def __init__(
#             self,
#             filename: str,
#             content_type: Optional[str] = None,
#             file: Optional[Union[bytes, str]] = None
#     ) -> None:
#         # Check if filename is an empty string
#         if filename == '':
#             # If filename is empty, set it to None
#             filename = None
#
#         # Call the constructor of the parent class with modified arguments
#         super().__init__(filename=filename, content_type=content_type, file=file)

# class CustomFormData(typing)

#add specific point to the rout
@app.post("/rout_points/")
async def add_rout_point(rout_id: int, description: str = None, lon: float = None, lat: float = None,
                         images: List[UploadFile] = File(None),
                         # images: List[Annotated[UploadFile, File(description="Some description")]] = None,
                         # images: Optional[List[Union[UploadFile, str]]] = None,
                         # images: Annotated[Union[bytes, None], List[Annotated[UploadFile, File()]]] = None,
                         audio: Optional[UploadFile] = File(None)):
    """

    :param rout_id: id of rout that point added to
    :param description: plaint text description of point
    :param lon:longitude of point
    :param lat: latitude of point
    :param images: images for point
    :param audio: audio for point
    :return: {'record': 'done'} if succeed else Exception

    """
    # saving files
    if isinstance(images, str):
        images = []
    print(images, audio)
    if images or audio:
        try:
            if images:
                if type(images) != list:
                    images = [images]
                for image in images:
                    contents_i = image.file.read()
                    with open(MEDIA_DIR+'/images/'+image.filename, 'wb+') as f_i:
                        f_i.write(contents_i)
            if audio:
                contents_a = audio.file.read()
                with open(MEDIA_DIR+'/audio/'+audio.filename, 'wb+') as f_a:
                    f_a.write(contents_a)
        except Exception as e:
            print(e)
            return {"message": "Error while uploading files"}
    else:
        images = None
        audio = None

    # select last rout point in rout
    r_query = select(rout_points).where(rout_points.columns.rout_id == rout_id).order_by(rout_points.columns.id.desc()).limit(1)
    last_rout_point = await database.fetch_one(r_query)

    # if current rout point is first in rout set previous id to 0 else to id of last point
    if last_rout_point:
        previous_point_id = last_rout_point.id
    else:
        previous_point_id = 0

    # write current point into database with values gotten from API
    coord = str([lon, lat])
    w_query = rout_points.insert().values(
        rout_id = rout_id,
        previous_point = previous_point_id,
        description = description,
        map_point = coord,
        images = str([image.filename if image != '' else None for image in images]) if images else None,
        audio = audio.filename if audio else None
    )
    current_point_id = await database.execute(w_query)

    # update previous point next_point filed with current point id
    u_query = update(rout_points).values(next_point=current_point_id).where(rout_points.columns.id == previous_point_id)
    await database.execute(u_query)
    return {'record': 'done'}

# get starting point
@app.get("/rout-points-first/{rout_id}/")
async def get_rout_point(rout_id: int) -> list:
    query = select(rout_points).where(rout_points.columns.rout_id == rout_id, rout_points.columns.previous_point==0)
    return await database.fetch_all(query)

# get specific point of the rout
@app.get("/rout-points/{rout_id}/{rout_point_id}")
async def get_rout_point(rout_id: int,rout_point_id: int) -> list:
    query = select(rout_points).where(rout_points.columns.rout_id == rout_id, rout_points.columns.id == rout_point_id)
    return await database.fetch_all(query)

@app.post("/keys/validate-key/{key}")
async def validate_key_api(key:str):
    if await validate_key(key):
        return Response(status_code=200)
    return Response(status_code=403, content='bad key')

@app.post("/keys/validate_user_key/{username}/{key}")
async def validate_user_key_api(username:str, key:str):
    if await validate_user_key(username, key):
        return Response(status_code=200)
    return Response(status_code=403)

@app.post("/users/activate/{username}")
async def paymnet_activation(username:str):
    query_user = update(users).values(access_granted=True).where(users.columns.username == username)
    await database.execute(query_user)
    return Response(status_code=200, content='Activated')

@app.post("/users/activate/{username}/{key}")
async def activate_user(username:str, key: Optional[str]) -> Response:
    print('starting check')
    if await validate_key(key):
        print('key valid')
        if await validate_user_key(username, key):
            print('user key valid')
            query_user = update(users).values(access_granted=True).where(users.columns.username == username)
            await database.execute(query_user)
            query_key = update(keys).values(used=True).where(keys.columns.key==key)
            await database.execute(query_key)
            return Response(status_code=200, content='Activated')
        return Response(status_code=403, content='Token not mathing user')
    return Response(status_code=403, content='Invalid Token or Token Taken')


# HTML TEMPLATES

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse(
        name='index.html', context={'request': request}
    )

@app.post("/", response_class=HTMLResponse)
async def err_loging(request: Request, error: str = None):
    return templates.TemplateResponse(
        name='index.html', context={'request': request, 'error': error}
    )

@app.post("/login-web/", response_class=HTMLResponse)
async def cabinet(request: Request, telegram_id: Annotated[str, Form()] = None):
    query = select(admins).where(admins.columns.chat_id == telegram_id)
    admin = await database.fetch_one(query)
    if admin:
        response = RedirectResponse(url='/cabinet/', status_code=303)
        response.set_cookie(key='user_id', value=telegram_id)
        return response
    return RedirectResponse(url="/?error=Отказ в доступе")

@app.get('/cabinet/', response_class=HTMLResponse)
async def cabinet(request: Request):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return RedirectResponse(url='/?error=Отказ в доступе')
    return templates.TemplateResponse(
        name='cabinet.html', context={'request': request}
    )