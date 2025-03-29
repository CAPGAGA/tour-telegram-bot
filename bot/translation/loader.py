import gettext
from functools import lru_cache

LOCALE_DIR = 'lang'
DEFAULT_LOCALE = 'en'

@lru_cache(maxsize=None)
def get_translator(lang_code: str):
    """Get gettext translator with fallback."""
    translator = gettext.translation(
        domain='messages',
        localedir=LOCALE_DIR,
        languages=[lang_code],
        fallback=True
    )
    return translator.gettext