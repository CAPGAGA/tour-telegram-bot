import hashlib
import hmac
import string

from sql import database, keys, users
import requests
from settings import BASE_URL
import asyncio
import random
from datetime import datetime
from urllib.parse import urlencode, quote

from sqlalchemy.sql import select

from settings import PRODAMUS_TOKEN

def get_id_of_rout(routs: list[dict], rout: str) -> int:
    for rout_dict in routs:
        if rout_dict.get('rout_name') == rout:
            return int(rout_dict.get('id'))
    return None

# generate key for user
async def generate_hash_key(chat_id):
    # Ensure chat_id is a string and strip unnecessary spaces to avoid discrepancies
    chat_id_str = str(chat_id).strip()

    # Explicitly specify the hashing algorithm and encoding (SHA-256, UTF-8)
    sha256_hash = hashlib.sha256(chat_id_str.encode('utf-8')).hexdigest()

    return sha256_hash

async def generate_promo():

    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(8))

async def generate_access_key(username):

    chars = string.ascii_uppercase + string.digits
    seed_slat = datetime.now().strftime("%Y%m%d%H%M%S%f")

    random.seed(username+seed_slat)

    key = ''.join(random.choice(chars) for _ in range(16))

    formatted_key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])

    return formatted_key


# validate key
async def validate_key(key):
    query = select(keys).where(keys.columns.key == key, keys.columns.used == False)
    result = await database.fetch_one(query)
    print(result)
    if result:
        return True
    return False

# validate key for user
async def validate_user_key(username, key):
    query = select(users).where(users.columns.username == username, users.columns.user_reg_hash == key)
    result = await database.fetch_one(query)
    if result:
        return True
    return False

async def delete_msg(update, context, msgs):
    if isinstance(msgs, int):
        msgs = [msgs]

    for msg in msgs:
        try:
            await context.bot.delete_message(chat_id=update.callback_query.message.chat_id,
                                         message_id=msg)
        except:
            Exception("Msg wasn't rendered on time of deletion... Skipping...")
