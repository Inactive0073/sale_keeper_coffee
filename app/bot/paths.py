from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parent

CUSTOMER_MENU_MEDIA_DIR = BASE_DIR / "dialogs" / "customer_user" / "media" / "menu"
WAITER_MEDIA_DIR = BASE_DIR / "dialogs" / "waiter" / "media"
RU_LOCALE_PATH = BASE_DIR / "locales" / "ru" / "LC_MESSAGES" / "txt.ftl"
EN_LOCALE_PATH = BASE_DIR / "locales" / "en" / "LC_MESSAGES" / "txt.ftl"

logger = logging.getLogger(__name__)
logger.debug(f"Waiter`s media folder path is: {WAITER_MEDIA_DIR}")
