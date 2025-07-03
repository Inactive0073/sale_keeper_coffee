from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_kb(*data: tuple[tuple[str, str]], width=1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.adjust(width)
    for el in data:
        text, url = el
        builder.add(InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()
