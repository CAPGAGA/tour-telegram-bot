import os
from pathlib import Path

# init .env file
from dotenv import load_dotenv
dotenv_path = os.path.join(Path(__file__).resolve().parent, '.env')
print(dotenv_path)
load_dotenv(dotenv_path)

BASE_URL = str(os.getenv("BASE_URL"))

TELEGRAM_TOKEN = str(os.getenv("TELEGRAM_TOKEN"))
# don't run debug in production!
DEBUG = os.getenv("DEBUG") == 'True'

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = os.path.join(Path(__file__).resolve().parent, 'media')

DATABASE_URL = os.getenv("DATABASE_URL")
