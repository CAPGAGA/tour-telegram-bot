import asyncio
import html
import json
import traceback

import httpx

import threading
import time
from datetime import datetime

import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    InputMediaPhoto,
    WebAppInfo, Bot
)
from telegram.ext import (
    ContextTypes,
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    PicklePersistence,
    PreCheckoutQueryHandler
)
from telegram.error import BadRequest
from telegram.constants import ParseMode
import requests
import logging

import copy

from decimal import Decimal

from settings import MEDIA_DIR, TELEGRAM_TOKEN, BASE_URL, PAYMENT_TOKEN
from handlers import (
    delete_msg,
    generate_access_key,
    generate_hash_key
)

from prodamus import generate_payment_link

from defaults import zemun_path

from paymnet.invoice_handler import prepare_payment_invoice
# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

filter_logger = logging.getLogger("filter_logger")

# Global variable to track the last time 'getUpdates' was logged
last_getupdates_time = datetime.now()

# # Function to log activity and update last request time if 'getUpdates' is found
# class GetUpdatesFilter(logging.Filter):
#     def filter(self, record):
#         global last_getupdates_time
#         message = record.getMessage()
#         # Check specifically for 'getUpdates' in the log message
#         if "getUpdates" in message:
#             last_getupdates_time = datetime.now()
#             filter_logger.info(f"Updated last_getupdates_time to {last_getupdates_time} after detecting 'getUpdates'")
#         return True
#
# # Add custom filter to logger
# get_updates_filter = GetUpdatesFilter()
# logger.addFilter(get_updates_filter)
#
# # Async function to send the alert message
# async def send_alert_async():
#     filter_logger.warning("Inactivity alert: No 'getUpdates' log in the last 5 minutes!")
#     alert_bot = Bot(token=TELEGRAM_TOKEN)
#     try:
#         await alert_bot.send_message(chat_id=295055548, text="Inactivity alert: No 'getUpdates' requests in the last 5 minutes!")
#     except Exception as e:
#         logger.error(f"Failed to send alert: {e}")
#
# # Wrapper function to run the async alert in a synchronous context
# def send_alert():
#     asyncio.run(send_alert_async())
#
# # Background function to monitor inactivity
# def monitor_inactivity():
#     global last_getupdates_time
#     while True:
#         time.sleep(60)  # Check every minute
#         time_since_last_update = (datetime.now() - last_getupdates_time).total_seconds()
#         if time_since_last_update > 5 * 60:  # 5 minutes
#             send_alert()
#
# # Start the monitoring thread
# monitor_thread = threading.Thread(target=monitor_inactivity, daemon=True)
# monitor_thread.start()

# Function to schedule message deletion
async def delete_message_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int = 3600):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Failed to delete message {message_id}: {e}")

# Helper function to generate route buttons
def generate_route_buttons(routs_data):
    buttons = [
        [InlineKeyboardButton(text=rout.get('rout_name'), callback_data=f'rout_{rout.get("id")}')]
        for rout in routs_data
    ]
    return buttons

# Helper function to send subscription options
async def send_subscription_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton('Хочу оплатить', callback_data='get_subscription')],
        [InlineKeyboardButton('У меня есть промокод', callback_data='get_promo_subscription')],
        [InlineKeyboardButton('У меня есть подарочный сертификат', callback_data='get_subscription_from_friend')],
        [InlineKeyboardButton('Хочу купить подарочный сертификат', callback_data='get_subscription_friend')]
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        'Похоже у тебя ещё нет доступа, ты можешь получить её нажав на кнопку ниже!',
        reply_markup=markup
    )

async def generate_payment_buttons(query):

    buttons = [
        [InlineKeyboardButton("Оплата российской картой", callback_data="ru_card")],
        [InlineKeyboardButton("Оплата зарубежной картой", callback_data="noru_card")],
    ]
    await query.message.reply_text("Какой картой будет проводиться оплата?", reply_markup=InlineKeyboardMarkup(buttons))

async def generate_payment_buttons_u(update):
    buttons = [
        [InlineKeyboardButton("Оплата российской картой", callback_data="ru_card")],
        [InlineKeyboardButton("Оплата зарубежной картой", callback_data="noru_card")],
    ]
    await update.message.reply_text("Какой картой будет проводиться оплата?", reply_markup=InlineKeyboardMarkup(buttons))

# command handlers
# /start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f'{BASE_URL}register-user/{update.message.from_user["username"]}/?chat_id={update.message.chat.id}',
            timeout=10, follow_redirects=True
        )
        routs = await client.get(
            url=f'{BASE_URL}routs',
            timeout=10, follow_redirects=True
        )

    if r.json().get('user') == 'with access':
        buttons = generate_route_buttons(routs.json())
        rout_choose = await update.message.reply_text(
            'Добро пожаловать снова! У тебя уже есть доступ\n\nДоступные маршруты:',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        context.user_data['to_delete'] = [rout_choose.id]

    elif r.json().get('user') == 'without access':
        await send_subscription_options(update, context)


# Function to activate subscription and return available routes
async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    key = update.message.text
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{BASE_URL}users/activate/{username}/{key}', follow_redirects=True)

        if r.status_code in [403, 500]:
            return await update.message.reply_text(f'Похоже произошла ошибка: {r.content}')

    routs = requests.get(url=f'{BASE_URL}routs')
    buttons = generate_route_buttons(routs.json())
    return await update.message.reply_text('Твой аккаунт успешно активирован!',
                                           reply_markup=InlineKeyboardMarkup(buttons))


# Function to check subscription status and send options accordingly
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{BASE_URL}get-user/{update.message.from_user.username}', follow_redirects=True)
        user = r.json()

        if user.get('access_granted'):
            async with httpx.AsyncClient() as client:
                routs = await client.get(url=f'{BASE_URL}routs/', follow_redirects=True)
            buttons = generate_route_buttons(routs.json())
            rout_choose = await update.message.reply_text(
                'У тебя уже есть доступ ко всем моим экскурсиям',
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            context.user_data['to_delete'] = [rout_choose.id]
            return

    await send_subscription_options(update, context)

# Send payment request to admins
async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        async with httpx.AsyncClient() as client:
            r = await client.get(f'{BASE_URL}check_access/{query.message.chat.username}/', follow_redirects=True)
            if r.status_code != 500 and r.json().get('user') == 'with access':
                return await query.message.reply_text('У тебя уже есть доступ! Используй команду /routs для просмотра маршрутов.')

        if query.data == 'get_subscription':
            context.user_data['buying'] = 'self'
            await generate_payment_buttons(query)
    else:
        async with httpx.AsyncClient() as client:
            r = await client.get(f'{BASE_URL}check_access/{update.message.chat.username}/', follow_redirects=True)
            if r.status_code != 500 and r.json().get('user') == 'with access':
                return await update.message.reply_text(
                    'У тебя уже есть доступ! Используй команду /routs для просмотра маршрутов.')

        await generate_payment_buttons_u(update)


# Payment handler for Russian cards
async def ru_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Prepare the invoice
    invoice = await prepare_payment_invoice(
        payment_type="ru_card",
        payment_reason=context.user_data.get('buying'),
        discount_type=context.user_data.get('discount_type', None),
        discount=context.user_data.get('discount', None)
    )

    # Check if invoice is None before proceeding
    if invoice is None:
        await query.message.reply_text("Произошла ошибка при создании счета. Перезапусти бота командой /start и попробуй снова")
        return

    # Send the invoice
    invoice_desc = await query.message.reply_text(
        'Ты получишь доступ к маршруту, оплатив его по кнопке ниже. '
        'После оплаты тебя ждут отмеченные на карте точки остановок, аудио- и фотоматериалы для погружения в тему.\n\nUživaj!'
    )
    invoice_body = await query.message.reply_invoice(**invoice)

    asyncio.create_task(delete_message_later(context, update.effective_chat.id, invoice_desc.id, 3600))

# Payment handler for non-Russian cards
async def noru_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    invoice = await prepare_payment_invoice(
        payment_type="noru_card",
        payment_reason=context.user_data.get('buying'),
        discount_type=context.user_data.get('discount_type', None),
        discount=context.user_data.get('discount', None)
    )

    chat_id = str(query.message.chat.id)
    secure_hash = str(await generate_hash_key(chat_id))

    if context.user_data.get('buying') == 'self':
        notification_link = f'http://49.13.167.190/prodamus-success/{chat_id}/{secure_hash}'
    elif context.user_data.get('buying') == 'friend':
        notification_link = f'http://49.13.167.190/prodamus-friend/{chat_id}/{secure_hash}'

    # Check if invoice is None before proceeding
    if invoice is None:
        await query.message.reply_text("Произошла ошибка при создании счета. Перезапусти бота командой /start и попробуй снова")
        return


    invoice.update({
        'urlSuccess': notification_link,
        'urlNotification': notification_link
    })



    payment_link = generate_payment_link(data=invoice)

    buttons = [[InlineKeyboardButton("Оплата зарубежной картой", web_app=WebAppInfo(url=payment_link))]]
    if context.user_data.get('discount_type', None):
        invoice_body = await query.message.reply_text("Для оплаты иностранными картами, нажми на кнопку ниже. \n\n"
                                       "<b>Цена указана в тенге и примерно эквивалента 1400 рублей + скидка.</b>",
                                       reply_markup=InlineKeyboardMarkup(buttons),
                                       parse_mode=ParseMode.HTML)
    else:
        invoice_body = await query.message.reply_text("Для оплаты иностранными картами, нажми на кнопку ниже. \n\n"
                                       "<b>Цена указана в тенге и примерно эквивалента 1400 рублей.</b>",
                                       reply_markup=InlineKeyboardMarkup(buttons),
                                       parse_mode=ParseMode.HTML)

    # delete after one hour
    asyncio.create_task(delete_message_later(context, update.effective_chat.id, invoice_body.id, 10))
    del context.user_data['buying']
    if context.user_data.get('discount_type'):
        del context.user_data['discount_type']
    if context.user_data.get('discount'):
        del context.user_data['discount']



# Function to handle friend gift purchase
async def get_subscription_for_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['buying'] = 'friend'
    await generate_payment_buttons(query)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != "Custom-Payload":
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)

async def process_success_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('buying') == 'self':
        username = update.message.from_user.username
        async with httpx.AsyncClient() as client:
            r = await client.post(f'{BASE_URL}users/activate/{username}', follow_redirects=True)

            if r.status_code == 403 or r.status_code == 500:
                await update.message.reply_text(f'Похоже произошла ошибка: {r.content}')
                return
        async with httpx.AsyncClient() as client:
            routs = await client.get(url=f'{BASE_URL}routs/', follow_redirects=True)
        buttons = []
        for rout in routs.json():
            buttons.append([InlineKeyboardButton(text=rout.get('rout_name'),
                                                 callback_data=f'rout_{rout.get("id")}')])
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('Спасибо за покупку доступа к боту!\n\n'
                                        'Ниже я перечислил все доступные на данный момент маршруты', reply_markup=markup, parse_mode='HTML')
        del context.user_data['buying']
        if context.user_data.get('discount_type'):
            del context.user_data['discount_type']
        if context.user_data.get('discount'):
            del context.user_data['discount']
    elif context.user_data.get('buying') == 'friend':
        access_key = await generate_access_key(update.message.from_user.username)
        async with httpx.AsyncClient() as client:
            r = await client.post(f'{BASE_URL}gift_keys/?key={access_key}', follow_redirects=True)
            if r.status_code == 200:
                await update.message.reply_text(
                    f'Спасибо за покупку\n\n'
                    f'Это ключ который ты можешь отправить своему другу или подруге\n\n'
                    f'`{access_key}`\n\n'
                    f'Твой друг может активировать код сразу после отправки мне команды /start и нажав кнопку '
                    f'"У меня есть код от друга"', parse_mode=ParseMode.MARKDOWN_V2
                )
        del context.user_data['buying']
        if context.user_data.get('discount_type'):
            del context.user_data['discount_type']
        if context.user_data.get('discount'):
            del context.user_data['discount']


async def check_promocode_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        promo_start = await update.callback_query.message.reply_text("Введи промокод")
        context.user_data['to_delete'] = [promo_start.id]
        return 'next__check__promo'
    else:
        promo_start = await update.message.reply_text("Введи промокод")
        context.user_data['to_delete'] = [promo_start.id]
        return 'next__check__promo'

async def check_promocode_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{BASE_URL}promo/?source=bot&phrase={update.message.text}', follow_redirects=True)
        if r.status_code != 403:
            await update.message.reply_text('Промокод активирован!')

            if r.json().get('is_percent'):
                context.user_data['discount_type'] = 'is_percent'
                context.user_data['discount'] = r.json().get('percent')
            else:
                context.user_data['discount_type'] = 'not_percent'
                context.user_data['discount'] = r.json().get('price')

            context.user_data['buying'] = 'self'
            await generate_payment_buttons_u(update)

        elif r.status_code == 403:
            await update.message.reply_text(f'<b>{r.content.decode("UTF-8")}</b>\n\n'
                                            f'Проверь правильность написания промокода и введи его снова', parse_mode='HTML')
            return 'next__check__promo'

async def check_friend_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        await update.callback_query.message.reply_text('Для активации ключа, отправь его мне в ответном сообщении')

        return 'next__friend__key__confirmation'

async def friend_key_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        r = await client.get(f'{BASE_URL}gift_keys/?key={update.message.text}', follow_redirects=True)

        if r.status_code == 200:
            activation = requests.post(f'{BASE_URL}users/activate/{update.message.from_user.username}')
            if activation.status_code == 200:
                await update.message.reply_text('Доступ активирован! Для доступа к маршрутам используй команду /routs')
            return ConversationHandler.END
        elif r.status_code == 404:
            await update.message.reply_text('Похоже такого ключа не существует или он был использован, проверь правильность '
                                            'написания и пришли мне его снова')
            return 'next__friend__key__confirmation'

async def promo_check_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Отмена')
    return ConversationHandler.END

async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    async with httpx.AsyncClient() as client:
        r = await client.post(f'{BASE_URL}admins/?chat_id={chat_id}&username={username}', follow_redirects=True)
        if r.status_code == 200:
            await update.message.reply_text(f'@{username}, теперь ты админ и будешь получать заявки! Для логина в интерфейс: {chat_id}')
        else:
            await update.message.reply_text('Ошибка регистрации')

async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Для того чтобы сделать это, нажмите на это \n'
                                    f'А для другого нажмите на другое \n')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Привет! '
                                    f'Это бот «дашины маршруты». Вместе со мной ты сможешь прогуляться по'
                                    f'предложенному маршруту и услышать рассказ о том, что встретишь на пути. В любой'
                                    f'момент можешь взять паузу и вернуться к маршруту позже или в другой день.🥰'
                                    f'\n'
                                    f'\n'
                                    f'Данный бот был создан при поддержке команды <a href="https://www.quadevents.me">quadevents.me</a>',
                                    parse_mode='HTML')

# main loop for points of rout
# greeting message
async def greeting_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_choice = query.data.split('_')[1]

    async with httpx.AsyncClient() as client:
        routs = await client.get(f'{BASE_URL}routs', follow_redirects=True)

        rout = list(filter(lambda rout: rout.get('id') == int(user_choice), routs.json()))[0]

        context.user_data['rout_id'] = user_choice
        first_point = await client.get(f'{BASE_URL}rout-points-first/{user_choice}', follow_redirects=True)
        context.user_data['rout_point_id'] = first_point.json()[0].get('id')
        context.user_data['next_rout_point_id'] = first_point.json()[0].get('next_point', None)

    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Приступить', callback_data='next')]])

    msg_instructions = await update.callback_query.message.reply_text(
        f'Начало экскурсии "{rout.get("rout_name")}"\n\n'
        'Привет!\n\n'
        'Если это твоя первая экскурсия, пожалуйста, ознакомься с форматом дальнейших сообщений.\n\n'
        'Первым сообщением будет приветствие от Даши, где она кратко пройдется по тому, что тебя ожидает на экскурсии.\n\n'
        'Как только с ним ознакомишься или решишь пропустить, нажми на кнопку <b>"Приступить"</b> - это запустит экскурсию.\n\n'
        'После этого я скину тебе точку на карте в чате, а так же все материалы.\n\n'
        'Ты можешь прервать экскурсию в любой момент и вернуться к ней позже - я запомню последнюю точку и тебе не '
        'придется меня перезапускать!\n\n'
        '<i>Если всё же решишь закончить экскурсию совсем, напиши мне /end в любой момент.</i>',
        parse_mode='HTML',
        reply_markup=markup)

    msg_intro = await update.callback_query.message.reply_text('К слову, Дашины сообщения-рассказы выглядят так 😊')

    msg_intro_voice = await update.callback_query.message.reply_voice(
        voice=MEDIA_DIR+'/audio/'+first_point.json()[0].get('audio'),
        caption=first_point.json()[0].get('description', 'ошибочка'),
        protect_content=True
    )
    context.user_data['to_delete'] = [msg_instructions.id, msg_intro.id, msg_intro_voice.id]
    return 'map_point'

# map point message for rout
async def map_materials_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'next':
        async with httpx.AsyncClient() as client:
            current_point = await client.get(f'{BASE_URL}rout-points/{context.user_data["rout_id"]}/{context.user_data["next_rout_point_id"]}', follow_redirects=True)

        point_data = current_point.json()
        # await delete_msg(update, context, context.user_data['to_delete'])

        # set next point from prev step to current point
        context.user_data['rout_point_id'] = context.user_data["next_rout_point_id"]

        # set next point to next point from point data
        context.user_data["next_rout_point_id"] = point_data[0].get('next_point', None)
        cords = point_data[0].get('map_point').strip('][').split(', ')

        # send map
        text_map = await update.callback_query.message.reply_text('Карта следующей точки')
        map_msg = await update.callback_query.message.reply_location(
            longitude=cords[0],
            latitude=cords[1],
            protect_content=True
        )

        context.user_data['to_delete'] = [map_msg.id, text_map.id]

        if context.user_data['next_rout_point_id'] == None:
            markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('Оставить отзыв', callback_data='next__report__start')],
                    [InlineKeyboardButton('Закончить экскурсию', callback_data='end')]
                ]
            )
        else:
            markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('Следующая точка', callback_data='next')]
                ]
            )

        # photo or media group
        photos = point_data[0].get('images').strip("[]").replace(" ", "").replace("'", "").split(',')
        if len(photos) == 1:
            img_msg = await update.callback_query.message.reply_photo(
                photo=open(MEDIA_DIR + '/images/' + photos[0], 'rb'),
                protect_content=True
            )
            context.user_data['to_delete'].append(img_msg)
        elif len(photos) > 1:
            medias = []
            for photo in photos:
                medias.append(InputMediaPhoto(media=open(MEDIA_DIR + '/images/' + photo, 'rb')))
            img_msg = await update.callback_query.message.reply_media_group(media=medias,  protect_content=True)
            for msg in img_msg:
                context.user_data['to_delete'].append(msg)
        # voice msg
        voice_msg = await update.callback_query.message.reply_voice(
            voice=MEDIA_DIR + '/audio/' + point_data[0].get('audio'),
            reply_markup=markup,
            caption=point_data[0].get('description', 'ошибочка'),
            protect_content=True
        )
        context.user_data['to_delete'].append(voice_msg)

        if point_data[0].get('next_point', None):
            return 'map_point'
    elif query.data == 'end':

        await update.callback_query.message.reply_text('Большое спасибо за прослушивание')
        await update.callback_query.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')
        return ConversationHandler.END

    elif query.data == 'next__report__start':

        markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('Закончить экскурсию без отзыва', callback_data='end')]
            ]
        )

        await query.message.reply_text(
            'Чтобы оставить отзыв отправь мне в ответ текстовое сообщение',
            reply_markup=markup,
        )

        return 'next__save__report'
    else:
        raise ValueError('Unknown command')

async def save_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        await update.callback_query.message.reply_text('Большое спасибо за прослушивание')
        await update.callback_query.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')
        return ConversationHandler.END

    # form report for admin
    report = update.message.text

    report_full = (f'Новый отзыв от пользователя @{update.message.from_user.username}\n\n'
                   f'{report}')

    await context.bot.send_message(
        chat_id=68848139,
        text=report_full
    )

    await update.message.reply_text('Большое спасибо за прослушивание и за твой отзыв!')
    await update.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')

    return ConversationHandler.END

# async def audio_text_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#
#     if query.data == 'next':
#         await delete_msg(update, context, context.user_data['to_delete'])
#         current_point = requests.get(
#             f'{BASE_URL}rout-points/{context.user_data["rout_id"]}/{context.user_data["next_rout_point_id"]}')
#
#         point_data = current_point.json()
#
#         return 'map_point'

async def end_rout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await update.callback_query.message.reply_text('Большое спасибо за прослушивание')
        await update.callback_query.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')
        return ConversationHandler.END
    await update.message.reply_text('Большое спасибо за прослушивание')
    await update.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')
    return ConversationHandler.END


# error handler
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # send data to developer
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=295055548, text=message, parse_mode=ParseMode.HTML
    )

    # send message to user
    exception = context.error

    if isinstance(exception, BadRequest):
        if 'Voice_messages_forbidden' in str(exception):
            await update.effective_message.reply_text(
                "Пожалуйста, разрешите отправку голосовых сообщений и попробуйте снова. Начиная с команды /start"
            )


def start_polling():
    persistence = PicklePersistence(filepath="conversations")
    app = Application.builder().token(TELEGRAM_TOKEN).read_timeout(20).persistence(persistence).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(greeting_message, pattern=r"^rout_\d*$")],
        states={
            'map_point': [CallbackQueryHandler(map_materials_point)],
            'next__save__report': [MessageHandler(filters.TEXT & ~filters.COMMAND, save_report)],
            'end': [CallbackQueryHandler(end_rout)]
        },
        fallbacks=[CommandHandler('end', end_rout)]
    )

    promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_promocode_start, pattern='get_promo_subscription')
                      ],
        states={
            'next__check__promo': [MessageHandler(filters.TEXT & ~filters.COMMAND, check_promocode_end)]
        },
        fallbacks=[CommandHandler('cancel', promo_check_cancel)],
        allow_reentry=True
    )

    access_activation_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_friend_code, pattern='get_subscription_from_friend')],
        states={
            'next__friend__key__confirmation': [
                MessageHandler(filters.TEXT & ~filters.COMMAND, friend_key_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', promo_check_cancel)],
        allow_reentry=True

    )

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('about', about_command))
    app.add_handler(CommandHandler('check', check_subscription))
    app.add_handler(CommandHandler('routs', check_subscription))
    app.add_handler(CommandHandler('reg1q2w3e4r5t6y', register_admin))

    # Payments
    app.add_handler(CallbackQueryHandler(buy_subscription, pattern=r'^get_subscription$'))
    app.add_handler(CallbackQueryHandler(ru_pay, pattern=r"^ru_card$"))
    app.add_handler(CallbackQueryHandler(noru_pay, pattern=r"noru_card"))

    app.add_handler(CommandHandler('buy', buy_subscription))
    app.add_handler(CallbackQueryHandler(get_subscription_for_friend, pattern='get_subscription_friend'))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT & ~filters.COMMAND, process_success_payment))

    app.add_handler(promo_conv)
    app.add_handler(conv)
    app.add_handler(access_activation_conv)

    # error handler
    app.add_error_handler(handle_error)

    print('starting polling')

    app.run_polling()

if __name__ == '__main__':

    start_polling()