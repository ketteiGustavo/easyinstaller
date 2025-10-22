import gettext
import os
from typing import Callable

# Default language and domain
DEFAULT_LANG = 'en_US'
DOMAIN = 'easyinstaller'

# Path to the locales directory
LOCALE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'locales'
)

_translator: Callable[[str], str] = gettext.gettext


def _(message: str) -> str:
    """
    Translate a message using the currently configured translator.
    """
    return _translator(message)


def setup_i18n(lang: str = DEFAULT_LANG):
    """
    Sets up the gettext translation system for the specified language.
    """
    global _translator
    try:
        # Ensure the locale directory exists
        if not os.path.isdir(LOCALE_DIR):
            os.makedirs(LOCALE_DIR, exist_ok=True)

        # Bind the domain to the locale directory
        gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
        gettext.textdomain(DOMAIN)

        # Create a translation object for the specified language
        translation = gettext.translation(
            DOMAIN, LOCALE_DIR, languages=[lang], fallback=True
        )
        _translator = translation.gettext
    except Exception as e:
        # Fallback to a dummy translation function if setup fails
        print(f'Warning: Could not set up i18n: {e}. Falling back to English.')
        _translator = gettext.gettext


# Initialize with default language
setup_i18n(DEFAULT_LANG)
