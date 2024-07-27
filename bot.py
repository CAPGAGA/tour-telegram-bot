import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    InputMediaPhoto,
    WebAppInfo
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
    PreCheckoutQueryHandler)
from telegram.constants import ParseMode
import requests
import logging

from decimal import Decimal

from settings import MEDIA_DIR, TELEGRAM_TOKEN, BASE_URL, PAYMENT_TOKEN
from handlers import (
    delete_msg,
    generate_access_key,
    generate_hash_key
)

from prodamus import generate_payment_link

from defaults import zemun_path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    r = requests.post(f'{BASE_URL}register-user/{update.message.from_user["username"]}/?chat_id={update.message.chat.id}')
    routs = requests.get(url=f'{BASE_URL}routs')

    # user with access
    if r.json().get('user', None) == 'with access':
        buttons = []
        for rout in routs.json():
            buttons.append([InlineKeyboardButton(text=rout.get('rout_name'), callback_data=f'rout_{rout.get("id")}')])
        rout_choose = await update.message.reply_text(
            f'Добро пожаловать снова! У тебя уже есть доступ'
            f'\n\n'
            f'Доступные маршруты:',
            reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data['to_delete'] = [rout_choose.id]

    # user without access
    elif r.json().get('user', None) == 'without access':

        buttons = [
        [InlineKeyboardButton('Хочу оплатить', callback_data='get_subscription')],
        [InlineKeyboardButton('У меня есть промокод', callback_data='get_promo_subscription')],
        [InlineKeyboardButton('У меня есть подарочный сертификат', callback_data='get_subscription_from_friend')],
        [InlineKeyboardButton('Хочу купить подарочный сертификат', callback_data='get_subscription_friend')]
               ]
        markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(f'Добро пожаловать снова! \n'
                                        f'К сожалению, ты не оплатил(-а) доступ к боту в прошлый раз, ты можешь сделать это '
                                        f'по кнопке снизу!👇',
                                        parse_mode='HTML',
                                        reply_markup=markup)
    # new user
    elif r.json().get('id'):
        buttons = [[InlineKeyboardButton('Хочу оплатить', callback_data='get_subscription')]]
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(f'Добро пожаловать в бот «дашины маршруты»! \n'
                                        f'Чтобы получить доступ к маршруту по Земуну, нажми кнопку «Хочу оплатить». '
                                        f'Если у тебя есть промокод или подарочный сертификат, '
                                        f'нажимай соответствующую кнопку.',
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

        markup = InlineKeyboardMarkup(buttons)
        rout_choose = await update.message.reply_text(
            'У тебя уже есть доступ и есть доступ ко всем моим экскурсиям',
            reply_markup=markup
        )
        context.user_data['to_delete'] = [rout_choose.id]
        return

    buttons = [
        [InlineKeyboardButton('Хочу оплатить', callback_data='get_subscription')],
        [InlineKeyboardButton('У меня есть промокод', callback_data='get_promo_subscription')],
        [InlineKeyboardButton('У меня есть подарочный сертификат', callback_data='get_subscription_from_friend')],
        [InlineKeyboardButton('Хочу купить подарочный сертификат', callback_data='get_subscription_friend')]
               ]
    markup = InlineKeyboardMarkup(buttons)

    return await update.message.reply_text('Похоже у тебя ещё нет доступа, ты можешь получить её нажав на кнопку ниже!'
                                           , reply_markup=markup)

async def send_request_to_admins(update: Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    r = requests.get(f'{BASE_URL}check_access/{update.callback_query.message.chat.username}/')
    if r.status_code != 500:
        if r.json().get('user') == 'with access':
            return await update.callback_query.message.reply_text(
                'У тебя уже есть доступ! Используй команду /routs чтобы получить список маршрутов'
            )

    if query.data == 'get_subscription':
        buttons = [
            [InlineKeyboardButton("Оплата российской картой", callback_data="ru_card")],
            [InlineKeyboardButton("Оплата зарубежной картой", callback_data="noru_card")],
        ]
        markup = InlineKeyboardMarkup(buttons)

        return await update.callback_query.message.reply_text("Какой картой будет проводиться оплата?",
                                               reply_markup=markup)


async def ru_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ru_card":
        invoice_desc = await update.callback_query.message.reply_text(
            'Ты получишь доступ к маршруту, оплатив его по кнопке ниже. '
            'После оплаты тебя ждут отмеченные на карте точки остановок, '
            'аудиорассказы о том, что тебя будет окружать и дополнительные '
            'материалы для более глубокого погружения в тему.\n\n'
            'Uživaj!'
        )

        invoice = await update.callback_query.message.reply_invoice(

            title='Доступ к боту',
            description='Доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.',
            payload='Custom-Payload',
            currency='RUB',
            prices=[LabeledPrice('Доступ к боту', 1400 * 100)],
            need_name=False,
            need_phone_number=False,
            is_flexible=False,
            provider_token=str(PAYMENT_TOKEN),
            need_email=True,
            send_email_to_provider=True,
            provider_data={
                "receipt":{
                    "items": [
                        {
                            "description": 'Доступ к боту дашины маршруты',
                            "quantity": "1.00",
                            "amount":
                                {
                                    "value": "1400.00",
                                    "currency": "RUB"
                                },
                            "vat_code": 1
                        }

                    ]
                }
            }

        )
        context.user_data['to_delete'] = [invoice_desc.id, invoice.id]
        context.user_data['buying'] = 'self'

async def noru_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "noru_card":
        chat_id = str(update.callback_query.message.chat.id)
        secure_hash = str(await generate_hash_key(chat_id))
        notification_link = f'http://49.13.167.190/prodamus-success/{chat_id}/{secure_hash}'
        data = zemun_path
        data['urlNotification'] = notification_link
        print(data)
        payment_link = generate_payment_link(data=data)
        print(payment_link)
        buttons = [
            [InlineKeyboardButton("Оплата зарубежной картой",
                                         web_app=WebAppInfo(url= payment_link
                                         )
                                  )
             ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.callback_query.message.reply_text("Для оплаты иностранными картами, нажми на кнопку ниже",
                                                        reply_markup=reply_markup
                                                       )


async def get_subscription_for_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await update.callback_query.message.reply_text('После оплаты по кнопке снизу, я пришлю тебе одноразовый ключ, '
                                                   'а так же инструкцию по его активации')

    invoice = await update.callback_query.message.reply_invoice(

        title='Доступ к боту для друга',
        description='Доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.',
        payload='Custom-Payload',
        currency='RUB',
        prices=[LabeledPrice('Доступ к боту', 1400 * 100)],
        need_name=False,
        need_phone_number=False,
        need_email=True,
        is_flexible=False,
        provider_token=str(PAYMENT_TOKEN),
        send_email_to_provider=True,
        provider_data= {
            "receipt": {
                "items": [
                    {
                        "description": 'Доступ к боту "дашины маршруты" для друга',
                        "quantity": "1.00",
                        "amount" :
                            {
                                "value": "1400.00",
                                "currency": "RUB"
                            },
                        "vat_code" : 1
                    }

                ]
            }
        }

    )
    context.user_data['buying'] = 'friend'

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
    await delete_msg(update, context, context.user_data["to_delete"])
    if context.user_data.get('buying') == 'self':
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
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('Спасибо за покупку доступа к боту!\n\n'
                                        'Ниже я перечислил все доступные на данный момент маршруты', reply_markup=markup, parse_mode='HTML')
        del context.user_data['buying']
    elif context.user_data.get('buying') == 'friend':
        access_key = await generate_access_key(update.message.from_user.username)
        r = requests.post(f'{BASE_URL}gift_keys/?key={access_key}')
        if r.status_code == 200:
            await update.message.reply_text(
                f'Спасибо за покупку\n\n'
                f'Это ключ который ты можешь отправить своему другу или подруге\n\n'
                f'`{access_key}`\n\n'
                f'Твой друг может активировать код сразу после отправки мне команды /start и нажав кнопку '
                f'"У меня есть код от друга"', parse_mode=ParseMode.MARKDOWN_V2
            )
        del context.user_data['buying']


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
    r = requests.get(f'{BASE_URL}promo/?source=bot&phrase={update.message.text}')

    if r.status_code != 403:
        await update.message.reply_text('Промокод активирован!')
        if r.json().get('is_percent'):
            new_price = Decimal('1400') * (Decimal('1') - Decimal(f'0.{r.json().get("percent")}'))
        else:
            new_price = r.json().get('price')
        invoice = await update.message.reply_invoice(

            title='Доступ к боту(ПРОМО)',
            description='Доступ к закрытому телеграм-боту с маршрутом по городу, в который входят отмеченные на карте точки и аудио- и фотоматериалы к каждой из них.',
            payload='Custom-Payload',
            currency='RUB',
            prices=[LabeledPrice('Доступ к боту', int(new_price) * 100)],
            need_name=False,
            need_phone_number=False,
            need_email=True,
            is_flexible=False,
            provider_token=str(PAYMENT_TOKEN),
            send_email_to_provider=True,
            provider_data={
                "receipt": {
                    "items": [
                        {
                            "description": 'Доступ к боту "дашины маршруты" (ПРОМО)',
                            "quantity": "1.00",
                            "amount":
                                {
                                    "value": f'{int(new_price)}.00',
                                    "currency": "RUB"
                                },
                            "vat_code": 1
                        }

                    ]
                }
            }

        )
        context.user_data['buying'] = 'self'
        return ConversationHandler.END

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

    r = requests.get(f'{BASE_URL}gift_keys/?key={update.message.text}')

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

    msg_instructions = await update.callback_query.message.reply_text(
        f'Начало экскурсии "{rout.get("rout_name")}"\n\n'
        f'Привет!\n\n'
        f'Если это твоя первая экскурсия, пожалуйста, ознакомься '
        f'с форматом дальнейших сообщений\n\n'
        f'Первым сообщением будет приветствие от Даши, где она кратко пройдется по тому, что тебя ожидает на экскурсии.\n\n '
        f'Как только с ним ознакомишься '
        f'или решишь пропустить, нажми на кнопку <b>"Приступить"</b> это запустит экскурсию \n\n'
        f'После этого я скину тебе точку на карте прямо в чате, а так же все материалы\n\n'
        f'Ты можешь прервать экскурсию в любой момент и вернуться к ней позже - '
        f'я запомню последнюю точку и тебе не придется меня перезапускать!\n\n'
        f'<i>Если всё же решишь закончить экскурсию совсем, напиши мне <b>/end</b> в любой момент </i>',
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
        current_point = requests.get(f'{BASE_URL}rout-points/{context.user_data["rout_id"]}/{context.user_data["next_rout_point_id"]}')

        point_data = current_point.json()
        # await delete_msg(update, context, context.user_data['to_delete'])

        # set next point from prev step to current point
        context.user_data['rout_point_id'] = context.user_data["next_rout_point_id"]

        # set next point to next point from point data
        context.user_data["next_rout_point_id"] = point_data[0].get('next_point', None)
        cords = point_data[0].get('map_point').strip('][').split(', ')
        text_map = await update.callback_query.message.reply_text('Карта следующей точки')
        map_msg = await update.callback_query.message.reply_location(
            longitude=cords[0],
            latitude=cords[1],
            protect_content=True
        )

        context.user_data['to_delete'] = [map_msg.id, text_map.id]

        if context.user_data['next_rout_point_id'] == None:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Закончить экскурсию', callback_data='end')]])
        else:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton('Следующая точка', callback_data='next')]])

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

    promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_promocode_start, pattern=r'^get_promo_subscription$')
        ],
        states= {
            'next__check__promo': [MessageHandler(filters.TEXT & ~filters.COMMAND, check_promocode_end)]
        },
        fallbacks=[CommandHandler('cancel', promo_check_cancel)],
        allow_reentry=True
    )

    access_activation_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(check_friend_code, pattern='get_subscription_from_friend')],
        states={
            'next__friend__key__confirmation': [MessageHandler(filters.TEXT & ~filters.COMMAND, friend_key_confirmation)]
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


    app.add_handler(CallbackQueryHandler(send_request_to_admins, pattern=r'^get_subscription$'))
    app.add_handler(CallbackQueryHandler(ru_pay, pattern=r"^ru_card$"))
    app.add_handler(CallbackQueryHandler(noru_pay, pattern=r"noru_card"))

    # app.add_handler(MessageHandler(filters.Regex(r'^\b[a-fA-F0-9]{64}\b$') & ~filters.COMMAND, activate_subscription))

    # Payments
    app.add_handler(CommandHandler('buy', send_request_to_admins))
    app.add_handler(CallbackQueryHandler(get_subscription_for_friend, pattern='get_subscription_friend'))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT & ~filters.COMMAND, process_success_payment))

    app.add_handler(promo_conv)
    app.add_handler(conv)
    app.add_handler(access_activation_conv)

    print('starting polling')
    app.run_polling()