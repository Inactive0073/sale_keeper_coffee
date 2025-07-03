from datetime import datetime
from nats.js import JetStreamContext
from nats.js.errors import NoStreamResponseError

from aiogram.types import InlineKeyboardMarkup
import logging
import json


logger = logging.getLogger(__name__)


async def delay_message_sending(
    js: JetStreamContext,
    chat_id: int,
    text: str,
    subject: str,
    delay: int = 0,
    tz_label: str = "Europe/Moscow",
    tz_offset: int = 3,
    keyboard: InlineKeyboardMarkup = None,
    file_id: str = None,
    disable_notification: bool = True,
    has_spoiler: bool = False,
) -> None:
    payload = json.dumps(
        {
            "keyboard": keyboard,
            "text": text,
            "chat_id": chat_id,
            "delay": delay,
            "timestamp": datetime.now().isoformat(),
            "tz_label": tz_label,
            "tz_offset": tz_offset,
            "disable_notification": disable_notification,
            "has_spoiler": has_spoiler,
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    try:
        await js.publish(subject=subject, payload=payload, headers=headers)
    except (NoStreamResponseError, Exception) as e:
        logger.exception(
            (
                f"Произошла ошибка во время публикации сообщения в стрим.\n"
                f"Сообщение об ошибке: {e}\n"
                f"Содержание запроса: {subject=}\n{headers=}\n{payload=}\n"
            )
        )
        raise
