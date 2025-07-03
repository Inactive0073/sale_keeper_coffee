from typing import Callable, Awaitable, Dict, Any, cast

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import AsyncSession
from logging import getLogger

from app.bot.db.customer_requests import upsert_customer

logger = getLogger(__name__)


class TrackAllUsersMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.cache = TTLCache(
            maxsize=1000,
            ttl=60 * 60 * 6,  # 6 часов
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Говорим IDE, что event на самом деле – Message
        event = cast(Message, event)
        user_id = event.from_user.id

        # Надо обновить данные пользователя, если он не в кэше
        if user_id not in self.cache:
            session: AsyncSession = data["session"]
            logger.info(
                "Обновление данных пользователя",
                extra={
                    "user_id": user_id,
                    "username": event.from_user.username,
                    "first_name": event.from_user.first_name,
                },
            )
            await upsert_customer(
                session=session,
                telegram_id=event.from_user.id,
                first_name=event.from_user.first_name,
                last_name=event.from_user.last_name,
                username=event.from_user.username,
            )
            self.cache[user_id] = None
        return await handler(event, data)
