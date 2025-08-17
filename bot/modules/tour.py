from typing import Any

import aiohttp
import os

from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from bot.decorators.auth import user_auth
from settings import BASE_DIR

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

# Add at the top of the file with other constants
TOUR_MESSAGES = {}  # Dict to store message IDs for each chat

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

@user_auth
async def show_tour_point(
        update: Update,
        context: CallbackContext,
        user
):
    """
     Shows each tour point in recursion
    """
    _ = context._

    query = update.callback_query
    await query.answer()

    # first delete previous messages
    await cleanup_tour_messages(update.effective_chat.id, context)
    print(query.data)
    # start, mid, finish
    state = query.data.split('_')[0]
    # rout_id (for start state) or point_id (for mid and finish states)
    data = query.data.split('_')[2]

    # Extract previous point ID if present
    previous_point_id = None
    if len(query.data.split('_')) > 3:
        prev_id = query.data.split('_')[3]
        previous_point_id = prev_id if prev_id != 'None' else None

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
            await show_tour_point_map(update, context, point, _, previous_point_id)
        elif state == 'info':
            await show_tour_point_materials(update, context, point, _, previous_point_id)
        return

    # render last message
    keyboard = [
        [InlineKeyboardButton(text="⭐", callback_data=f"review_{data}_1")],
        [InlineKeyboardButton(text="⭐⭐", callback_data=f"review_{data}_2")],
        [InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"review_{data}_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"review_{data}_4")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"review_{data}_5")],
        [InlineKeyboardButton(text="🔙 "+ _("Review with comment"), callback_data=f"review_{data}_comment")],
        [InlineKeyboardButton(text="🔙 "+ _("Back to Menu"), callback_data="main_menu")]
    ]

    await update.callback_query.message.edit_text(_("Rate this tour"), reply_markup=InlineKeyboardMarkup(keyboard))
    return

async def cleanup_tour_messages(chat_id: int, context: CallbackContext):
    """Delete previous tour point messages"""
    if chat_id in TOUR_MESSAGES:
        for message_id in TOUR_MESSAGES[chat_id]:
            try:
                await context.bot.delete_message(chat_id, message_id)
            except Exception:
                pass  # Ignore errors if message was already deleted
        TOUR_MESSAGES[chat_id] = []

async def show_tour_point_map(
        update: Update,
        context: CallbackContext,
        point: dict,
        _: Any,
        previous_point_id: str
):
    """Renders point message by updating existing message and cleaning up old ones"""
    chat_id = update.effective_chat.id

    # Initialize message list for this chat if needed
    if chat_id not in TOUR_MESSAGES:
        TOUR_MESSAGES[chat_id] = []

    upper_border = '➖' * MAP_MESSAGE_WITH_EMOJI
    description = (f"{upper_border}"
                   f"\n           <a href="">&#8204;</a>🧭 <b>"+ _("Map of next point") + "</b>")
    
    # Send description and store message ID
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=description,
        parse_mode=ParseMode.HTML
    )
    TOUR_MESSAGES[chat_id].append(message.message_id)

    # Send location if available
    latitude = point.get("latitude")
    longitude = point.get("longitude")

    if latitude and longitude:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        _("I am here!"),
                        callback_data=f"info_mytour_{point['id']}_{previous_point_id}"
                    )
                ]
            ]
        )
        location_message = await context.bot.send_location(
            chat_id=chat_id,
            latitude=latitude,
            longitude=longitude,
            reply_markup=reply_markup
        )
        TOUR_MESSAGES[chat_id].append(location_message.message_id)

async def show_tour_point_materials(
        update: Update,
        context: CallbackContext,
        point: dict,
        _: Any,
        previous_point_id: str
):
    """Shows point materials and cleans up previous messages"""
    chat_id = update.effective_chat.id
    
    # Initialize message list for this chat if needed
    if chat_id not in TOUR_MESSAGES:
        TOUR_MESSAGES[chat_id] = []

    # Handle audios
    audios = point.get("audio", [])
    if isinstance(audios, list) and audios:
        for audio in audios:
            audio_path = os.path.join(BASE_DIR, 'web/media/audio', audio)
            audio_name = _("Stop") + ' ' + point.get('point_name')
            if os.path.isfile(audio_path):
                with open(audio_path, 'rb') as audio_file:
                    message = await context.bot.send_audio(
                        chat_id,
                        audio=audio_file,
                        filename=audio_name,
                        performer='PocketTourBot',
                        protect_content=True
                    )
                    TOUR_MESSAGES[chat_id].append(message.message_id)

    # Handle images
    images = point.get("image", [])
    if isinstance(images, list) and images:
        media_group = [
            InputMediaPhoto(
                media=open(os.path.join(BASE_DIR, 'web/media/images', img), 'rb')
            ) for img in images
        ]
        messages = await context.bot.send_media_group(chat_id, media_group, protect_content=True)
        for message in messages:
            TOUR_MESSAGES[chat_id].append(message.message_id)

    # Setup navigation controls
    keyboard = []
    current_point_id = point['id']

    if point.get("next_point"):
        keyboard.append([InlineKeyboardButton("➡️ " + _("Next Point"), callback_data=f"mid_mytour_{point['next_point']}_{current_point_id}")])
        keyboard.append([InlineKeyboardButton("⬅️ " + _("Previous Point"), callback_data=f"mid_mytour_{previous_point_id}")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ " + _("Previous Point"), callback_data=f"mid_mytour_{previous_point_id}")])
        keyboard.append([InlineKeyboardButton("⭐ " + _("Leave review!"), callback_data=f"review_mytour_{point['rout_id']}")])
        keyboard.append([InlineKeyboardButton("✅ " + _("To main menu"), callback_data="main_menu")])

    # Send navigation controls
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(
        chat_id,
        text="🔄 " + _("Tour navigation:"),
        reply_markup=reply_markup
    )
    TOUR_MESSAGES[chat_id].append(message.message_id)