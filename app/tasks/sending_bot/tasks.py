import asyncio
import logging
import taskiq_aiogram

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, ContentType
from aiogram import exceptions

from taskiq import TaskiqDepends

from ...taskiq_broker.broker import broker

logger = logging.getLogger(__name__)

taskiq_aiogram.init(
    broker,
    "app.main:dp",
    # This is path to the bot instance.
    "app.main:bot",
    # You can specify more bots here.
)


async def safe_send(
    bot: Bot,
    telegram_id: int,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    file_id: str = None,
    content_type: ContentType = None,
    disable_notification: bool = True,
    has_spoiler: bool = False,
) -> bool:
    try:
        if file_id is None:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                reply_markup=keyboard,
                disable_notification=disable_notification,
            )
        elif content_type == ContentType.PHOTO:
            await bot.send_photo(
                chat_id=telegram_id,
                photo=file_id,
                caption=text,
                has_spoiler=has_spoiler,
                reply_markup=keyboard,
                disable_notification=disable_notification,
            )
        elif content_type == ContentType.VIDEO:
            await bot.send_video(
                chat_id=telegram_id,
                video=file_id,
                caption=text,
                has_spoiler=has_spoiler,
                reply_markup=keyboard,
                disable_notification=disable_notification,
            )
        else:
            logging.warning(f"[{telegram_id}] Unsupported content type: {content_type}")
            return False

        return True  # успешно отправлено

    except exceptions.TelegramBadRequest:
        logging.warning(f"[{telegram_id}] BadRequest: чат не найден")
    except exceptions.TelegramForbiddenError:
        logging.warning(f"[{telegram_id}] Forbidden: бот заблокирован пользователем")
    except exceptions.TelegramRetryAfter as e:
        logging.warning(
            f"[{telegram_id}] Flood control: повтор через {e.retry_after} сек."
        )
        await asyncio.sleep(e.retry_after)
        return await safe_send(  # Рекурсивный повтор
            bot,
            telegram_id,
            text,
            keyboard,
            file_id,
            content_type,
            disable_notification,
            has_spoiler,
        )
    except exceptions.TelegramAPIError:
        logging.exception(f"[{telegram_id}] Telegram API Error")
    return False


@broker.task(task_name="push_msg_to_bot_now")
async def send_message_bot_subscribers(
    telegram_ids: list[int],
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    file_id: str = None,
    content_type: ContentType = None,
    disable_notification: bool = True,
    has_spoiler: bool = False,
    bot: Bot = TaskiqDepends(),
    **kwargs,
) -> None:
    if not telegram_ids:
        logger.warning("Список telegram_ids пуст, сообщения не отправлены")
        return

    sent_messages = 0

    for chat_id in telegram_ids:
        ok = await safe_send(
            bot=bot,
            telegram_id=chat_id,
            text=text,
            keyboard=keyboard,
            file_id=file_id,
            content_type=content_type,
            disable_notification=disable_notification,
            has_spoiler=has_spoiler,
        )
        if ok:
            sent_messages += 1

        await asyncio.sleep(0.05)  # Limit: 20 msg/sec

    logger.info(f"Успешно отправлено {sent_messages} из {len(telegram_ids)} сообщений")


@broker.task(task_name="push_msg_to_bot_later")
async def send_schedule_message_bot_subscribers(
    telegram_ids: list[int],
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    file_id: str = None,
    content_type: ContentType = None,
    disable_notification: bool = True,
    has_spoiler: bool = False,
    bot: Bot = TaskiqDepends(),
    **kwargs,
) -> None:
    sent = 0

    for telegram_id in telegram_ids:
        ok = await safe_send(
            bot=bot,
            telegram_id=telegram_id,
            text=text,
            keyboard=keyboard,
            file_id=file_id,
            content_type=content_type,
            disable_notification=disable_notification,
            has_spoiler=has_spoiler,
        )
        if ok:
            sent += 1
        await asyncio.sleep(0.05)  # Telegram API rate-limit

    logger.info(f"Успешно отправлено {sent} сообщений из {len(telegram_ids)}")
