import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).parent

DEBUG = True if str(os.getenv("DEBUG", "False")) == "True" else False

# auth settings
SECRET_KEY: str = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60*24*30 #30 days

# paypal settings
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_API_URL = os.getenv("PAYPAL_API_URL", "https://api-m.sandbox.paypal.com")

POSTGRES_HOST= os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_USER= os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD= os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_PORT= os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB= os.getenv('POSTGRES_DB', 'pocketour')