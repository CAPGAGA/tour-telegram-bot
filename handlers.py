import hashlib
from sql import database, keys, users
import requests
from settings import BASE_URL
import asyncio

from sqlalchemy.sql import select

def get_id_of_rout(routs: list[dict], rout: str) -> int:
    for rout_dict in routs:
        if rout_dict.get('rout_name') == rout:
            return int(rout_dict.get('id'))
    return None

# generate key for user
async def generate_hash_key(chat_id):
    key = hashlib.sha256(bytes(chat_id)).hexdigest()
    return str(key)

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


# # check key for user
# async def activate_user(username, key):
#     if await validate_key(key):
#         if await validate_user_key(username, key):
#             pass
#         return -1
#     return -2