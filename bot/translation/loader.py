import gettext
import os.path
from functools import lru_cache
from pathlib import Path

LOCALE_DIR = os.path.join(Path(__file__).parent.parent.parent, 'lang')
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