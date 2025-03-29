import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).parent

DEBUG = True if str(os.getenv("DEBUG", "False")) == "True" else False

SUPPORTED_LANGUAGES = ['ru', 'en']

HEADLESS_MODE: bool = True if str(os.getenv("HEADLESS_MODE", "False")) == "True" else False

SUPPORTED_PAYMENT_METHODS = []
if os.getenv("IS_PAYPAL_ON", "False") == "True":
    SUPPORTED_PAYMENT_METHODS.append("paypal")

if os.getenv("IS_YUUKASSA_TELEGRAM_ON", "False") == "True":
    SUPPORTED_PAYMENT_METHODS.append("yuukassa_telegram")

# auth settings
SECRET_KEY: str = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60*24*30 #30 days

# paypal settings
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_API_URL = os.getenv("PAYPAL_API_URL", "https://api-m.sandbox.paypal.com")

# telegram setting

TELEGRAM_PAYMENT_PROVIDER = os.getenv("TELEGRAM_PAYMENT_PROVIDER")
TELEGRAM_CURRENCY = os.getenv('TELEGRAM_CURRENCY')

POSTGRES_HOST= os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_USER= os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD= os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_PORT= os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB= os.getenv('POSTGRES_DB', 'pocketour')

CURRENCY_CONVERTER_API_KEY = os.getenv('CURRENCY_CONVERTER_API_KEY')