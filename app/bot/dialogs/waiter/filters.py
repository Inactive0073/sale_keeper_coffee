from aiogram.types import Message


def filter_web_app(message: Message):
    return message.web_app_data is not None
