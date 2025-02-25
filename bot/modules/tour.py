import aiohttp
import os

from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from api.settings import BASE_DIR

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

async def fetch_first_tour_point(rout_id):
    """
        Fetch first tour point from API
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                    f"{API_BASE_URL}/rout-points/get-first-point",
                    params={"rout_id": rout_id}
            ) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None


async def fetch_tour_point(point_id):
    """
        Fetch individual tour point from API
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                    f"{API_BASE_URL}/rout-points/get-detailed-rout-point",
                    params={"rout_point_id": point_id}
            ) as response:
                if response.status != 200:
                    return None
                return await response.json()
        except aiohttp.ClientError:
            return None


async def show_tour_point(update: Update, context: CallbackContext):
    """
     Shows each tour point in recursion
    """
    query = update.callback_query
    await query.answer()
    # start, mid, finish
    state = query.data.split('_')[0]
    # rout_id or point_id
    data = query.data.split('_')[-1]

    point = None

    if state == 'start':
        # this is first point so we fetch first point with rout_id
        point = await fetch_first_tour_point(data)
    elif state == 'end':
        # this is last point show review button and exit
        point = None
    elif state == 'mid':
        # mid of tour so we fetch point with point_id
        point = await fetch_tour_point(data)
    else:
        ValueError('Invalid state')

    if point:
        # render point
        await render_point_message(update, context, point)
        return

    # render last message


async def render_point_message(update: Update, context: CallbackContext, point: dict):
    """
        Renders point message
    """

    chat_id = update.effective_chat.id
    # send point description
    description = f"📃 {point.get('point_text', '***')}"
    await context.bot.send_message(
        chat_id=chat_id,
        text=description,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # send point map
    latitude = point.get("latitude")
    longitude = point.get("longitude")

    # send map with point
    if latitude and longitude:
        await context.bot.send_location(chat_id, latitude=latitude, longitude=longitude)

    # check and send audios if needed
    audios = point.get("audio", [])
    if isinstance(audios, list) and audios:
        for audio in audios:
            audio_path =  os.path.join(BASE_DIR, 'crm/media/audio', audio)
            await context.bot.send_audio(
                chat_id,
                audio=audio_path,
                filename=f'Point {point["id"]} audio'
            )
    # check and send images if needed
    images = point.get("image", [])
    if isinstance(images, list) and images:
        media_group = [
            InputMediaPhoto(
                media=open(os.path.join(BASE_DIR, 'crm/media/images', img), 'rb')
            ) for img in images
        ]
        await context.bot.send_media_group(chat_id, media_group)

    # setup controller
    keyboard = []
    if point.get("next_point"):
        keyboard.append([InlineKeyboardButton("➡️ Next Point", callback_data=f"mid_mytour_{point['next_point']}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Finish Tour", callback_data="end_mytour_0")])

    # send controller
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, text='🔄 Tour navigation:', reply_markup=reply_markup)