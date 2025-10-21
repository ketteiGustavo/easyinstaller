import gettext
import os

# Default language and domain
DEFAULT_LANG = 'en_US'
DOMAIN = 'easyinstaller'

# Path to the locales directory
LOCALE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'locales'
)


def setup_i18n(lang: str = DEFAULT_LANG):
    """
    Sets up the gettext translation system for the specified language.
    """
    try:
        # Ensure the locale directory exists
        if not os.path.isdir(LOCALE_DIR):
            os.makedirs(LOCALE_DIR, exist_ok=True)

        # Bind the domain to the locale directory
        gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
        gettext.textdomain(DOMAIN)

        # Set the locale for the current thread/process
        # This might not be strictly necessary for gettext.gettext to work
        # but it's good practice for other locale-aware functions.
        # However, setting LC_ALL can have side effects, so we'll rely on
        # the translation object directly.

        # Create a translation object for the specified language
        global _
        _ = gettext.translation(
            DOMAIN, LOCALE_DIR, languages=[lang], fallback=True
        ).gettext

    except Exception as e:
        # Fallback to a dummy translation function if setup fails
        print(f'Warning: Could not set up i18n: {e}. Falling back to English.')
        _ = lambda s: s  # noqa: E731


# Initialize with default language
setup_i18n(DEFAULT_LANG)
