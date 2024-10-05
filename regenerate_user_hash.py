import asyncio
from sql import database, users
from handlers import generate_hash_key


# Async function to update the hashes
async def update_hashes():
    # Connect to the database
    await database.connect()

    # Fetch all users
    query = users.select()
    users_ = await database.fetch_all(query)

    for user in users_:
        chat_id = user['id']
        new_hash = await generate_hash_key(chat_id)

        # Update the user's hash in the database
        update_query = users.update().where(users.c.id == chat_id).values(user_reg_hash=new_hash)
        await database.execute(update_query)

    # Close the database connection
    await database.disconnect()

# Run the script
if __name__ == "__main__":
    asyncio.run(update_hashes())
