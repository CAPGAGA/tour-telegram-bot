import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot, Invoice, LabeledPrice, InputMediaPhoto
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, PicklePersistence, PreCheckoutQueryHandler
import requests
import re
import json
from settings import MEDIA_DIR, DEBUG, TELEGRAM_TOKEN, BASE_URL, PAYMENT_TOKEN
from handlers import get_id_of_rout, generate_hash_key, delete_msg
import logging


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

    return await update.message.reply_text('Похоже у тебя ещё нет подписки, ты можешь получить её нажав на кнопку ниже!', reply_markup=markup)

async def send_request_to_admins(update: Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    r = requests.get(f'{BASE_URL}check_access/{update.callback_query.message.chat.username}/')
    if r.status_code != 500:
        if r.json().get('user') == 'with access':
            return await update.callback_query.message.reply_text('У тебя уже есть подписка! Используй команду /routs чтобы получить список маршрутов')

    if query.data == 'get_subscription':
        invoice_desc = await update.callback_query.message.reply_text('Для доступа к моим экскурсиям оплати доступ к боту нажав кнопку ниже \n\n'
                                                       'После оплаты ты получишь доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.')

        print(str(PAYMENT_TOKEN))
        invoice = await update.callback_query.message.reply_invoice(
            title='Доступ к боту',
            description='Доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.',
            payload='Custom-Payload',
            currency='RUB',
            prices=[LabeledPrice('Доступ к боту', 1000 * 100)],
            need_name=False,
            need_phone_number=False,
            need_email=True,
            # need_shipping_address=False,
            is_flexible=False,
            provider_token=str(PAYMENT_TOKEN),
            # provider_token='381764678:TEST:82486',
            send_email_to_provider=True,

        )
        context.user_data['to_delete'] = [invoice_desc.id, invoice.id]

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
    await delete_msg(update, context, context.user_data['to_delete'])
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
                                                   f'После этого я скину тебя точку на карте прямо в чате, а так же все материалы\n\n'
                                                   f'Ты можешь прервать экскурсию в любой момент и вернуться к ней позже - '
                                                   f'я запомню последнюю точку и тебе не придется меня перезапускать!\n\n'
                                                   f'<i>Если всё же решишь закончить экскурсию совсем, напиши мне <b>/end</b> в любой момент </i>', parse_mode='HTML', reply_markup=markup)
    msg_intro = await  update.callback_query.message.reply_text('К слову, Дашины сообщения-рассказы выглядят так 😊')
    msg_intro_voice = await update.callback_query.message.reply_voice(voice=MEDIA_DIR+'/audio/'+first_point.json()[0].get('audio'), caption=first_point.json()[0].get('description', 'ошибочка'))
    context.user_data['to_delete'] = [msg_instructions.id, msg_intro.id, msg_intro_voice.id]
    return 'map_point'

# map point message for rout
async def map_materials_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'next':
        current_point = requests.get(f'{BASE_URL}rout-points/{context.user_data["rout_id"]}/{context.user_data["next_rout_point_id"]}')

        point_data = current_point.json()
        # await delete_msg(update, context, context.user_data['to_delete'])

        # set next point from prev step to current point
        context.user_data['rout_point_id'] = context.user_data["next_rout_point_id"]

        # set next point to next point from point data
        context.user_data["next_rout_point_id"] = point_data[0].get('next_point', None)
        cords = point_data[0].get('map_point').strip('][').split(', ')
        text_map = await update.callback_query.message.reply_text('Карта следующей точки')
        map_msg = await update.callback_query.message.reply_location(longitude=cords[0], latitude=cords[1])

        context.user_data['to_delete'] = [map_msg.id, text_map.id]

        if context.user_data['next_rout_point_id'] == None:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Закончить экскурсию', callback_data='end')]])
        else:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Следующая точка', callback_data='next')]])

        # photo or media group
        photos = point_data[0].get('images').strip("[]").replace(" ", "").replace("'", "").split(',')
        if len(photos) == 1:
            img_msg = await update.callback_query.message.reply_photo(photo=open(MEDIA_DIR + '/images/' + photos[0], 'rb'))
            context.user_data['to_delete'].append(img_msg)
        elif len(photos) > 1:
            medias = []
            for photo in photos:
                medias.append(InputMediaPhoto(media=open(MEDIA_DIR + '/images/' + photo, 'rb')))
            img_msg = await update.callback_query.message.reply_media_group(media=medias)
            for msg in img_msg:
                context.user_data['to_delete'].append(msg)
        # voice msg
        voice_msg = await update.callback_query.message.reply_voice(
        voice=MEDIA_DIR + '/audio/' + point_data[0].get('audio'), reply_markup=markup, caption=point_data[0].get('description', 'ошибочка'))
        context.user_data['to_delete'].append(voice_msg)
        # next_point_msg = await update.callback_query.message.reply_text('Следующая точка', )
        if point_data[0].get('next_point', None):
            return 'map_point'
        return 'end'

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

    print('starting polling')
    app.run_polling()