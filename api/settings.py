import os
from pathlib import Path

# auth settings
SECRET_KEY: str = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60*24*30 #30 days

BASE_DIR: str = Path(__file__).parent.parent