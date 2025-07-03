from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import Message
from fluentogram import TranslatorRunner

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type: ignore

# Инициализация роутера уровня модуля
other_router = Router(name=__name__)


# Хендлер будет срабатывать на любые сообщения справкой
@other_router.message()
async def send_echo(message: Message, i18n: TranslatorRunner) -> None:
    await message.answer(i18n.no.handle())
