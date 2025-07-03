from aiogram.filters import BaseFilter
from aiogram.types import Message


class ContactFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.contact.user_id == message.chat.id
