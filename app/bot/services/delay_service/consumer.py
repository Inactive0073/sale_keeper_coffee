import asyncio
import logging
import json
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from environs import Env

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError, TelegramRetryAfter

from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext

logger = logging.getLogger(__name__)
env = Env()


class DelayedMessageConsumer:

    def __init__(
        self,
        nc: Client,
        js: JetStreamContext,
        bot: Bot,
        subject: str,
        stream: str,
        durable_name: str,
    ) -> None:
        self.nc = nc
        self.js = js
        self.bot = bot
        self.subject = subject
        self.stream = stream
        self.durable_name = durable_name
        self.stream_sub = None

    async def on_message_channel(self, msg: Msg):
        logger.info("Получено сообщение для канала")

        try:
            payload = json.loads(msg.data.decode("utf-8"))

            chat_id = payload.get("chat_id")
            post_message = payload.get("text")
            keyboard_data = payload.get("keyboard")
            delay = payload.get("delay", 0)
            tz_offset = payload.get("tz_offset", 0)
            disable_notification = payload.get("disable_notification")
            sent_time_str = payload.get("timestamp")

            tz_info = timezone(timedelta(hours=tz_offset))
            sent_time = datetime.fromisoformat(sent_time_str).replace(tzinfo=tz_info)

            if sent_time + timedelta(seconds=delay) > datetime.now(tz=tz_info):
                new_delay = (sent_time + timedelta(seconds=delay) - datetime.now(tz=tz_info)).total_seconds()
                logger.info(f"Отложено повторно на {new_delay:.1f} сек.")
                await msg.nak(delay=new_delay)
                return

            await asyncio.sleep(0.07)  # ⬅️ ограничение 15 сообщений/сек

            try:
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=post_message,
                    reply_markup=keyboard_data,
                    disable_notification=disable_notification,
                )
                logger.info(f"Канал: сообщение {message.message_id} отправлено в {chat_id}")
                await msg.ack()
            except TelegramRetryAfter as e:
                logger.warning(f"Flood control (канал): спим {e.retry_after} сек.")
                await asyncio.sleep(e.retry_after)
                await msg.nak(delay=e.retry_after)

        except Exception as e:
            logger.exception("Ошибка при обработке сообщения для канала")
            await msg.term()

    async def on_message_bot(self, msg: Msg):
        logger.info("Получено сообщение для подписчика")

        try:
            payload = json.loads(msg.data.decode("utf-8"))

            chat_id = payload.get("chat_id")
            post_message = payload.get("text")
            keyboard_data = payload.get("keyboard")
            delay = payload.get("delay", 0)
            tz_offset = payload.get("tz_offset", 0)
            disable_notification = payload.get("disable_notification")
            sent_time_str = payload.get("timestamp")

            tz_info = timezone(timedelta(hours=tz_offset))
            sent_time = datetime.fromisoformat(sent_time_str).replace(tzinfo=tz_info)

            if sent_time + timedelta(seconds=delay) > datetime.now(tz=tz_info):
                new_delay = (sent_time + timedelta(seconds=delay) - datetime.now(tz=tz_info)).total_seconds()
                await msg.nak(delay=new_delay)
                return

            await asyncio.sleep(0.07)  # ⬅️ тоже здесь ограничиваем

            try:
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=post_message,
                    reply_markup=keyboard_data,
                    disable_notification=disable_notification,
                )
                logger.info(f"Бот: сообщение {message.message_id} отправлено в {chat_id}")
                await msg.ack()
            except TelegramRetryAfter as e:
                logger.warning(f"Flood control (бот): спим {e.retry_after} сек.")
                await asyncio.sleep(e.retry_after)
                await msg.nak(delay=e.retry_after)
            except TelegramBadRequest:
                logger.warning(f"BadRequest — бот не может писать в чат {chat_id}")
            except TelegramAPIError as e:
                logger.error(f"Ошибка Telegram API: {e}")

        except Exception as e:
            logger.exception(f"Ошибка при обработке сообщения бота: {e}")
            await msg.term()

    async def unsubscribe(self) -> None:
        if self.stream_sub:
            await self.stream_sub.unsubscribe()
            logger.info(
                "Отписка от потока сообщений",
                extra={
                    "subject": self.subject,
                    "stream": self.stream,
                },
            )
