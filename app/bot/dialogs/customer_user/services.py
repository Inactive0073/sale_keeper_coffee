from aiogram.types import (
    ContentType,
    FSInputFile,
)

from datetime import datetime as dt
from app.bot.paths import CUSTOMER_MENU_MEDIA_DIR
from aiogram.utils.media_group import MediaGroupBuilder
import logging
import re
from os import path


logger = logging.getLogger(__name__)


def check_birthday_format(birthday: str) -> str:
    return dt.strptime(birthday, "%d.%m.%Y").strftime("%d.%m.%Y")


def convert_media_to_group():
    album_builder = MediaGroupBuilder()
    for i in range(1, 11):
        try:
            file_path = CUSTOMER_MENU_MEDIA_DIR / f"{i}.jpg"
            if not path.isfile(file_path):
                break
            album_builder.add(type=ContentType.PHOTO, media=FSInputFile(path=file_path))
        except Exception as e:
            logger.error(
                f"Произошла ошибка при попытке создать медиа альбом. Ошибка: {e}"
            )
    return album_builder.build()


def normalize_phone_number(phone_number: str) -> str:
    """Приводит телефон к виду 7XXXXXXXXXX (только цифры, без +)"""
    digits_only = re.sub(r"\D", "", phone_number)  # Удаляем все нецифры
    if digits_only.startswith("8"):
        digits_only = "7" + digits_only[1:]
    elif digits_only.startswith("7"):
        digits_only = "7" + digits_only[1:]
    return digits_only