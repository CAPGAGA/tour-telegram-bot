import aiohttp
import os

from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from api.settings import BASE_DIR

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/apiV1")

# underscore width of different messages (_)
# Max width of text message
MAX_MESSAGE_WIDTH = 68
MAX_MESSAGE_WITH_EMOJI=17
# Width of map widget
MAP_MESSAGE_WIDTH = 36
MAP_MESSAGE_WITH_EMOJI = 13
# Width of message with 1 photos
MEDIA_GROUP_1_WIDTH = 68
MEDIA_GROUP_1_WITH_EMOJI = 17
# Width of message with 4 photos
MEDIA_GROUP_4_WIDTH = 50
MEDIA_GROUP_4_WITH_EMOJI = 25
# Width of message with 5 photos
MEDIA_GROUP_5_WIDTH = 68
MEDIA_GROUP_5_WIDTH_EMOJI = 17

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
    elif state == 'review':
        # this is last point show review button and exit
        point = None
    elif state == 'mid' or state == 'info':
        # mid of tour so we fetch point with point_id
        point = await fetch_tour_point(data)
    else:
        ValueError('Invalid state')

    if point:
        # render point
        if state == 'mid' or state == 'start':
            await show_tour_point_map(update, context, point)
        elif state == 'info':
            await show_tour_point_materials(update, context, point)
        return

    # render last message
    keyboard = [
        [InlineKeyboardButton(text="⭐", callback_data="review_{data}_1")],
        [InlineKeyboardButton(text="⭐⭐", callback_data="review_{data}_2")],
        [InlineKeyboardButton(text="⭐⭐⭐", callback_data="review_{data}_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="review_{data}_4")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="review_{data}_5")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="main_menu")]
    ]
    await update.callback_query.message.edit_text('Rate this tour', reply_markup=InlineKeyboardMarkup(keyboard))
    return


async def show_tour_point_map(update: Update, context: CallbackContext, point: dict):
    """
        Renders point message
    """

    chat_id = update.effective_chat.id
    upper_border = '➖' * MAP_MESSAGE_WITH_EMOJI
    # send point description
    description = (f"{upper_border}"
                   f"\n           <a href="">&#8204;</a>🧭 <b>Map of next point</b>")
    await context.bot.send_message(
        chat_id=chat_id,
        text=description,
        parse_mode=ParseMode.HTML
    )
    # send point map
    latitude = point.get("latitude")
    longitude = point.get("longitude")

    # send map with point
    if latitude and longitude:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        'I am here!',
                        callback_data=f"info_mytour_{point['id']}"
                    )
                 ]
            ]
        )
        await context.bot.send_location(
            chat_id,
            latitude=latitude,
            longitude=longitude,
            reply_markup=reply_markup
        )
    return

async def show_tour_point_materials(
        update: Update,
        context: CallbackContext,
        point: dict
):
    chat_id = update.effective_chat.id

    # check and send audios if needed
    audios = point.get("audio", [])
    if isinstance(audios, list) and audios:
        for audio in audios:
            audio_path =  os.path.join(BASE_DIR, 'crm/media/audio', audio)
            audio_name = f"Audio for point {point.get('id')}"
            await context.bot.send_audio(
                chat_id,
                audio=audio_path,
                filename=audio_name,
                performer='PocketTourBot',
                protect_content=True
            )



    # check and send images if needed
    images = point.get("image", [])
    if isinstance(images, list) and images:
        media_group = [
            InputMediaPhoto(
                media=open(os.path.join(BASE_DIR, 'crm/media/images', img), 'rb')
            ) for img in images
        ]
        await context.bot.send_media_group(chat_id, media_group, protect_content=True)

    # setup controller
    keyboard = []
    if point.get("next_point"):
        keyboard.append([InlineKeyboardButton("➡️ Next Point", callback_data=f"mid_mytour_{point['next_point']}")])
    else:
        keyboard.append([InlineKeyboardButton("⭐ Leave review!", callback_data=f"review_mytour_{point['rout_id']}")])
        keyboard.append([InlineKeyboardButton("✅ To main menu", callback_data="main_menu")])

    # send controller
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, text='🔄 Tour navigation:', reply_markup=reply_markup)