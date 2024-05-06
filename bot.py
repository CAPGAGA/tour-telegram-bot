import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot, Invoice, LabeledPrice
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, PicklePersistence, PreCheckoutQueryHandler
import requests
import re
import json
from settings import MEDIA_DIR, DEBUG, TELEGRAM_TOKEN, BASE_URL
from handlers import get_id_of_rout, generate_hash_key, delete_msg
import logging

from yookassa import Configuration, Payment

Configuration.account_id = 506751
Configuration.secret_key = 538350


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)




# check if in DEBUG mode
print('running debug' if DEBUG else 'running prod')

# TODO move some api calls to global space

# command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    r = requests.post(f'{BASE_URL}register-user/{update.message.from_user["username"]}/?chat_id={update.message.chat.id}')
    routs = requests.get(url=f'{BASE_URL}routs')
    # user with access
    if r.json().get('user', None) == 'with access':
        buttons = []
        for rout in routs.json():
            buttons.append([InlineKeyboardButton(text=rout.get('rout_name'), callback_data=f'rout_{rout.get("id")}')])
        rout_choose = await update.message.reply_text(f'Добро пожаловать снова! Ваша подписка активна и вам открыт доступ ко всему '
                                        f'каталогу экскурсий!\n\n'
                                        f'Доступные маршруты:',
                                        reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data['to_delete'] = [rout_choose.id]
    # user without access
    elif r.json().get('user', None) == 'without access':
        if DEBUG:
            buttons = [[InlineKeyboardButton('Хочу подписку', callback_data='get_subscription')]]
            markup = InlineKeyboardMarkup(buttons)
        else:
            buttons = [[InlineKeyboardButton('Хочу подписку', callback_data='get_subscription')]]
            markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(f'Добро пожаловать снова! \n'
                                        f'К сожалению, ты не приобрел(-а) подписку в прошлый раз, ты можешь сделать это '
                                        f'оставив заявку по кнопке снизу!👇',
                                        parse_mode='HTML',
                                        reply_markup=markup)
    # new user
    elif r.json().get('id'):
        buttons = [[InlineKeyboardButton('Хочу подписку', callback_data='get_subscription')]]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(f'Добро пожаловать в дашины маршруты! \n'
                                        f'Для открытия полного функционала, пожалуйста оставь заявку по кнопке ниже.\n'
                                        f'Я постараюсь связаться с тобой как можно быстрее',
                                        parse_mode= 'HTML',
                                        reply_markup=markup)

async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.message.text
    username = update.message.from_user.username
    r = requests.post(f'{BASE_URL}users/activate/{username}/{key}')
    if r.status_code == 403 or r.status_code == 500:
        return await update.message.reply_text(f'Похоже произошла ошибка: {r.content}')

    routs = requests.get(url=f'{BASE_URL}routs')
    buttons = []
    for rout in routs.json():
        buttons.append([InlineKeyboardButton(text=rout.get('rout_name'), callback_data=f'rout_{rout.get("id")}')])

    markup = InlineKeyboardMarkup(buttons)

    return await update.message.reply_text('Твой аккаунт успешно активирован!', reply_markup=markup)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = requests.get(f'{BASE_URL}get-user/{update.message.from_user.username}')
    user = r.json()

    if user.get('access_granted'):
        routs = requests.get(url=f'{BASE_URL}routs/')
        buttons = []
        for rout in routs.json():
            buttons.append([InlineKeyboardButton(text=rout.get('rout_name'),
                                                 callback_data=f'rout_{rout.get("id")}')])
                                                 # callback_data=1)])
        markup = InlineKeyboardMarkup(buttons)
        rout_choose = await update.message.reply_text('У тебя активирована подписка и есть доступ ко всем моим экскурсиям', reply_markup=markup)
        context.user_data['to_delete'] = [rout_choose.id]
        return
    buttons = [[InlineKeyboardButton('Хочу подписку', callback_data='get_subscription')]]
    markup = InlineKeyboardMarkup(buttons)

    return await update.message.reply_text('Похоже у тебя ещё нет подписки, оставь заявку по кнопке снизу, и  я свяжусь с тобой как можно быстрее', reply_markup=markup)

async def send_request_to_admins(update: Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # print(update.callback_query.message.chat.username)
    r = requests.get(f'{BASE_URL}check_access/{update.callback_query.message.chat.username}/')
    # print(r)
    if r.status_code != 500:
        if r.json().get('user') == 'with access':
            return await update.callback_query.message.reply_text('У тебя уже есть подписка! Используй команду /routs чтобы получить список маршрутов')
    # key = await generate_hash_key(update.callback_query.message.chat.id)
    # if query.data == 'get_subscription':
    #     username = update.callback_query.message.chat.username
    #     r = requests.get(f'{BASE_URL}admins/')
    #     data = r.json()
    #     bot = Bot(TELEGRAM_TOKEN)
    #     for admin in data:
    #         chat_id = admin.get('chat_id', None)
    #         text = f'Новая заявка от @{username}!\nКлюч для регистрации: <b>{key}</b>'
    #         await bot.send_message(chat_id=chat_id, text=text,  parse_mode = 'HTML', disable_web_page_preview=True)
    #     await update.callback_query.message.reply_text('Заявка отправлена. Я свяжусь с тобой в ближайшее время.')
    if query.data == 'get_subscription':
        invoice_desc = await update.callback_query.message.reply_text('Для доступа к моим экскурсиям оплати доступ к боту нажав кнопку ниже \n\n'
                                                       'После оплаты ты получишь доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.')

        invoice = await update.callback_query.message.reply_invoice(
            title='Доступ к боту',
            description='Доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.',
            payload='Custom-Payload',
            currency='RUB',
            prices=[LabeledPrice('Доступ к боту', 850 * 100)],
            need_name=False,
            need_phone_number=False,
            need_email=True,
            # need_shipping_address=False,
            is_flexible=False,
            provider_token='381764678:TEST:82691',
            # provider_token='381764678:TEST:82486',
            send_email_to_provider=True,
            # provider_data= {
            #     "receipt": {
            #         "items": [
            #             {
            #                 'description': 'Доступ к боту',
            #                 'quantity': "1.00",
            #                 "amount": {
            #                     "value": "850.00",
            #                     "currency": "RUB"
            #                 },
            #                 "vat_code": 1
            #             }
            #         ]
            #     }
            # }
        )
        context.user_data['to_delete'] = [invoice_desc, invoice]

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
    username = update.message.from_user.username
    r = requests.post(f'{BASE_URL}users/activate/{username}')

    if r.status_code == 403 or r.status_code == 500:
        await update.message.reply_text(f'Похоже произошла ошибка: {r.content}')
        return

    routs = requests.get(url=f'{BASE_URL}routs/')
    buttons = []
    for rout in routs.json():
        buttons.append([InlineKeyboardButton(text=rout.get('rout_name'),
                                             callback_data=f'rout_{rout.get("id")}')])
        # callback_data=1)])
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('Спасибо за покупку доступа к боту!\n\n'
                                    'Ниже я перечислил все доступные на данный момент маршруты', reply_markup=markup, parse_mode='HTML')

async def register_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    r = requests.post(f'{BASE_URL}admins/?chat_id={chat_id}&username={username}')
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
                                    f'момент можешь взять паузу и вернуться к маршруту позже или в другой день.'
                                    f'\n'
                                    f'В данный момент у меня нет возможности принимать оплату картой, поэтому, пожалуйста напиши "сюда" или подожди, пока я сама тебе напишу🥰\n'
                                    f'Данный бот был создан при поддержке команды <a href="https://www.quadevents.me">quadevents.me</a>',
                                    parse_mode='HTML')

# async def test_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text('Testing audio')
#     await update.message.reply_voice(open(MEDIA_DIR+'/file_example_MP3_1MG.mp3', 'rb+'))
#
# # message handlers
# async def access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if "Проверить подписку" in update.message.text:
#         r = requests.get(f'{BASE_URL}check_access/{update.message.from_user["username"]}/')
#         if r.json().get('user') == 'without access':
#             buttons = [[KeyboardButton("Проверить подписку")]]
#             await update.message.reply_text(f'Пока ваша подписка не активна 😔 \n'
#                                             f'Возможно платеж ещё не прошёл, повторите подписку через 10 минут, если '
#                                             f'проблема продолжиться, пожалуйста свяжитесь с нами',
#                                             parse_mode='HTML',
#                                             reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#         elif r.json().get('user') == 'with access':
#             rr = requests.get(f'{BASE_URL}routs/')
#             buttons = [[]]
#             for rout in rr.json():
#                 buttons[0].append(KeyboardButton(text=rout.get('rout_name')))
#             # buttons = [[KeyboardButton("Экскурсия 1"), KeyboardButton("Экскурсия 2")]]
#             await update.message.reply_text(f'Ваша подписка активна 😎\n'
#                                             f'Большое спасибо, что выбрали нас 🥰\n'
#                                             f'Теперь вам доступны все наши экскурсии, снизу вы можете выбрать любую '
#                                             f'из них!',
#                                             parse_mode='HTML',
#                                             reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#
#     # activate test subscription !!! only accessible in DEBUG mode !!!
#     if DEBUG:
#         if 'Активация подписки' in update.message.text:
#             r = requests.post(f'{BASE_URL}test_access/{update.message.from_user["username"]}')
#             await update.message.reply_text('Тестовая подписка активна!')
#
# async def rout_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     routs = requests.get(url=f'{BASE_URL}routs')
#     rout_id = get_id_of_rout(routs=routs.json(), rout=update.message.text)
#     requests.post(url=f'{BASE_URL}set-user-rout/{update.message.from_user["username"]}/{rout_id}')
#     buttons = [[KeyboardButton('Начинаем!')]]
#     await update.message.reply_text(f'Выбрана экскурсия "{update.message.text}"',
#                                     parse_mode= 'HTML',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
#                                     )
#     await update.message.reply_voice(open(MEDIA_DIR+'/audio/'+'greeting.m4a', 'rb+'))
#
# async def start_rout(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = requests.get(url=f'{BASE_URL}get-user/{update.message.from_user["username"]}')
#     rout_points = requests.get(url=f'{BASE_URL}routs/{user.json().get("current_rout")}')
#     user_rout = user.json().get('current_rout')
#
#     # get first point of rout and set it us user current point
#     user_current_rout_point = rout_points.json()[0].get('id')
#     r = requests.post(url=f'{BASE_URL}set-user-rout-point/{update.message.from_user["username"]}/{user_current_rout_point}')
#     coords = json.loads(rout_points.json()[0].get('map_point'))
#
#     buttons = [[KeyboardButton('Материалы')]]
#
#     await update.message.reply_text(f'Отлично! Сейчас я пришлю тебе точку на карте. \n'
#                                     f'Как доберешься до нужного места - нажми на кнопку "Материалы" \n'
#                                     f'Я отправлю тебе все материалы \n'
#                                     f'\n'
#                                     f'Если захочешь закончить экскурсию и перейти к другой воспользуйся командой /end',
#                                     parse_mode='HTML',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#     await update.message.reply_location(longitude=coords[1], latitude=coords[0])
#
# async def next_point(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = requests.get(url=f'{BASE_URL}get-user/{update.message.from_user["username"]}')
#     # switch of user point
#     current_point = requests.get(url=f'{BASE_URL}rout-points/{user.json().get("current_rout_point")}')
#     next_point_id = current_point.json()[0].get('next_point')
#     next_point = requests.get(url=f'{BASE_URL}rout-points/{next_point_id}')
#     requests.post(url=f'{BASE_URL}set-user-rout-point/{update.message.from_user["username"]}/{next_point_id}')
#
#     coords = json.loads(next_point.json()[0].get('map_point'))
#
#     buttons = [[KeyboardButton('Материалы')]]
#
#     await update.message.reply_text(f'Карта следующей точки',
#                                     parse_mode= 'HTML',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#     await update.message.reply_location(longitude=coords[1], latitude=coords[0])
#
# async def previous_point(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
#     user = requests.get(url=f'{BASE_URL}get-user/{update.message.from_user["username"]}')
#     # switch of user point
#     current_point = requests.get(url=f'{BASE_URL}rout-points/{user.json().get("current_rout_point")}')
#     previous_point_id = current_point.json()[0].get('previous_point')
#     previous_point = requests.get(url=f'{BASE_URL}rout-points/{previous_point_id}')
#     requests.post(url=f'{BASE_URL}set-user-rout-point/{update.message.from_user["username"]}/{previous_point_id}')
#
#     coords = json.loads(previous_point.json()[0].get('map_point'))
#     buttons = [[KeyboardButton('Материалы')]]
#
#     await update.message.reply_text(f'Карта предыдущей точки',
#                                     parse_mode='HTML',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#     await update.message.reply_location(longitude=coords[1], latitude=coords[0])
#
# async def end_rout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user = requests.get(url=f'{BASE_URL}get-user/{update.message.from_user["username"]}')
#
#     # dropping rout and point of user to default -> 0
#     requests.post(url=f'{BASE_URL}set-user-rout/{update.message.from_user["username"]}/0')
#     requests.post(url=f'{BASE_URL}set-user-rout-point/{update.message.from_user["username"]}/0')
#
#     # send routs again
#     rr = requests.get(f'{BASE_URL}routs/')
#     buttons = [[]]
#     for rout in rr.json():
#         buttons[0].append(KeyboardButton(text=rout.get('rout_name')))
#
#     await update.message.reply_text(f'Вы закончили маршрут. Надеюсь вы получили только приятные впечатления '
#                                     f'Ниже я вывел для тебя наши другие экскурсии',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#
#
# async def render_materials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     # get user instance and user rout and point
#     user = requests.get(url=f'{BASE_URL}get-user/{update.message.from_user["username"]}')
#     current_rout_point = user.json().get('current_rout_point')
#     rout_point_materials = requests.get(url=f'{BASE_URL}rout-points/{current_rout_point}')
#     json_materials = rout_point_materials.json()[0]
#
#     # check if point is last in the rout and render next/previous point or end rout
#     buttons = [[]]
#     if json_materials.get('next_point') and json_materials.get('previous_point'):
#         buttons[0].append(KeyboardButton('Предыдущая точка'))
#         buttons[0].append(KeyboardButton('Следующая точка'))
#     elif json_materials.get('next_point'):
#         buttons[0].append(KeyboardButton('Следующая точка'))
#     else:
#         buttons[0].append(KeyboardButton('Предыдущая точка'))
#         buttons[0].append(KeyboardButton('Закончить экскурсию'))
#
#     # unpack single photo or list of photos
#     try:
#         photos = json_materials.get('images').strip("]['").split(', ')
#     except:
#         photos = json_materials.get('images')
#
#
#     await update.message.reply_text(f'{json_materials.get("description")}',
#                                     reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
#
#     # sending photos in list or single one
#     try:
#         for photo in photos:
#             await update.message.reply_photo(photo=MEDIA_DIR+'/images/'+photo.strip("'"))
#     except:
#         await update.message.reply_photo(photo=MEDIA_DIR+'/images/'+json_materials.get('images'))
#     await update.message.reply_voice(voice=MEDIA_DIR+'/audio/'+json_materials.get('audio'))



# main loop for points of rout

# greeting message
async def greeting_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await delete_msg(update, context, context.user_data['to_delete'])
    user_choice = query.data.split('_')[1]

    routs = requests.get(f'{BASE_URL}routs')

    rout = list(filter(lambda rout: rout.get('id') == int(user_choice), routs.json()))[0]

    context.user_data['rout_id'] = user_choice
    first_point = requests.get(f'{BASE_URL}rout-points-first/{user_choice}')
    context.user_data['rout_point_id'] = first_point.json()[0].get('id')
    context.user_data['next_rout_point_id'] = first_point.json()[0].get('next_point', None)

    markup = InlineKeyboardMarkup([[InlineKeyboardButton('Приступить', callback_data='next')]])

    msg_instructions = await update.callback_query.message.reply_text(f'Начало экскурсии "{rout.get("rout_name")}"\n\n'
                                                   f'Если это твоя первая экскурсия, пожалуйста, ознакомься '
                                                   f'с форматом дальнейших сообщений\n\n'
                                                   f'Первое сообщение будет приветствием от Даши, где она кратко пройдется '
                                                   f'по тому, что тебя ожидает на экскурсии.\n\nКак только с ним ознакомишься '
                                                   f'или решишь пропустить, нажми на кнопку <b>"Приступить"</b> это запустит экскурсию \n\n'
                                                   f'После этого я скину тебя точку на карте прямо в чате, как доберешься до нее,'
                                                   f'нажми на кнопку <b>"Я на месте"</b>, в ответ я скину Дашину лекцию, а так же фото материалы\n\n'
                                                   f'Ты можешь прервать экскурсию в любой момент и вернуться к ней позже - '
                                                   f'я запомню последнюю точку и тебе не придется меня перезапускать!\n\n'
                                                   f'<i>Если всё же решишь закончить экскурсию совсем, напиши мне <b>/end</b> в любой момент </i>', parse_mode='HTML', reply_markup=markup)
    msg_intro = await  update.callback_query.message.reply_text('К слову, Дашины сообщения-лекции выглядят так 😊')
    msg_intro_voice = await update.callback_query.message.reply_voice(voice=MEDIA_DIR+'/audio/'+first_point.json()[0].get('audio'))
    context.user_data['to_delete'] = [msg_instructions.id, msg_intro.id, msg_intro_voice.id]
    return 'map_point'

# map point message for rout
async def map_materials_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'next':
        current_point = requests.get(f'{BASE_URL}rout-points/{context.user_data["rout_id"]}/{context.user_data["next_rout_point_id"]}')

        point_data = current_point.json()
        await delete_msg(update, context, context.user_data['to_delete'])
        # set next point from prev step to current point
        context.user_data['rout_point_id'] = context.user_data["next_rout_point_id"]
        # set next point to next point from point data
        context.user_data["next_rout_point_id"] = point_data[0].get('next_point', None)
        cords = point_data[0].get('map_point').strip('][').split(', ')
        text_map = await update.callback_query.message.reply_text('Карта следующей точки')
        map_msg = await update.callback_query.message.reply_location(longitude=cords[0], latitude=cords[1])


        if context.user_data['next_rout_point_id'] == None:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Закончить экскурсию', callback_data='end')]])
        else:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Следующая точка', callback_data='next')]])
        photo = point_data[0].get('images').strip("[]'")
        voice_msg = await update.callback_query.message.reply_voice(
            voice=MEDIA_DIR + '/audio/' + point_data[0].get('audio'))
        img_msg = await update.callback_query.message.reply_photo(photo=open(MEDIA_DIR+'/images/'+photo, 'rb'), reply_markup=markup)
        # next_point_msg = await update.callback_query.message.reply_text('Следующая точка', )
        context.user_data['to_delete'] = [img_msg.id, voice_msg.id, map_msg.id, text_map.id]

        return 'map_point'

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
    await update.message.reply_text('Большое спасибо за прослушивание')
    await update.message.reply_text('Для просмотра остальных экскурсий используй команду /routs')
    return ConversationHandler.END

if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversations")
    app = Application.builder().token(TELEGRAM_TOKEN).read_timeout(20).persistence(persistence).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(greeting_message, pattern=r"^rout_\d*$")],
        states= {
            'map_point': [CallbackQueryHandler(map_materials_point)],
            # 'text_audio': [CallbackQueryHandler(audio_text_point)],
            'end': [CallbackQueryHandler(end_rout)]
        },
        fallbacks=[CommandHandler('end', end_rout)]
    )

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('about', about_command))
    app.add_handler(CommandHandler('check', check_subscription))
    app.add_handler(CommandHandler('routs', check_subscription))
    app.add_handler(CommandHandler('reg1q2w3e4r5t6y', register_admin))
    app.add_handler(CallbackQueryHandler(send_request_to_admins, pattern=r'^get_subscription$'))
    app.add_handler(MessageHandler(filters.Regex(r'^\b[a-fA-F0-9]{64}\b$') & ~filters.COMMAND, activate_subscription))

    # Payments
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT & ~filters.COMMAND, process_success_payment))

    app.add_handler(conv)
    # app.add_handler(CommandHandler('end', end_rout))
    # # DEBUG commands
    # if DEBUG:
    #     app.add_handler(CommandHandler('test_audio', test_audio))
    #
    # # Messages
    # if DEBUG:
    #     app.add_handler(
    #         MessageHandler(filters.Regex(re.compile(r'^Проверить подписку$|^Активация подписки$')), access_handler))
    # else:
    #     app.add_handler(
    #         MessageHandler(filters.Regex(re.compile(r'^Проверить подписку$')), access_handler))
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^test\d$", re.IGNORECASE)), rout_choice)) # TODO change filter in prod
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^Начинаем!$", re.IGNORECASE)), start_rout))
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^Материалы$", re.IGNORECASE)), render_materials))
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^Следующая точка$", re.IGNORECASE)), next_point))
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^Предыдущая точка$", re.IGNORECASE)), previous_point))
    # app.add_handler(MessageHandler(filters.Regex(re.compile(r"^Закончить экскурсию$", re.IGNORECASE)), end_rout))

    print('starting polling')
    app.run_polling()