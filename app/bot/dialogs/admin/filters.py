from aiogram.types import Message


def filter_message_to_find_username_or_id(message: Message):
    """Проверка на валидность имени в телеграм или Telegram ID"""
    return message.text.startswith("@") or message.text.isdigit()
