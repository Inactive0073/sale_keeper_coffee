import asyncio

from taskiq import TaskiqDepends

import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, ContentType
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramAPIError

from ...taskiq_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.task(task_name="push_msg_to_channel")
async def send_message_to_channel(
    text: str,
    channels: list[tuple[str, str]],
    keyboard: InlineKeyboardMarkup = None,
    file_id: str = None,
    content_type: ContentType = None,
    disable_notification: bool = True,
    has_spoiler: bool = False,
    bot: Bot = TaskiqDepends(),
    **kwargs,
) -> None:
    sent_messages = 0

    for channel in channels:
        channel_name = "@" + channel[0]

        try:
            if content_type is None:
                message = await bot.send_message(
                    chat_id=channel_name,
                    text=text,
                    reply_markup=keyboard,
                    disable_notification=disable_notification,
                )
            elif content_type == ContentType.PHOTO:
                message = await bot.send_photo(
                    chat_id=channel_name,
                    photo=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    has_spoiler=has_spoiler,
                    disable_notification=disable_notification,
                )
            elif content_type == ContentType.VIDEO:
                message = await bot.send_video(
                    chat_id=channel_name,
                    video=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    has_spoiler=has_spoiler,
                    disable_notification=disable_notification,
                )
            else:
                logger.warning(f"Unsupported content type: {content_type}")
                continue

            logger.info(f"Сообщение {message.message_id} успешно отправлено в {channel_name}.")
            sent_messages += 1
            await asyncio.sleep(0.07)  # 15 сообщений в секунду

        except TelegramRetryAfter as e:
            logger.warning(f"Flood control: sleeping for {e.retry_after} sec.")
            await asyncio.sleep(e.retry_after)
        except TelegramBadRequest:
            logger.error(f"BadRequest: чат {channel_name} не найден или бот не имеет доступа.")
        except TelegramAPIError as e:
            logger.exception(f"Ошибка Telegram API при отправке в {channel_name}: {e}")

    logger.info(f"Всего успешно отправлено: {sent_messages} из {len(channels)}.")
