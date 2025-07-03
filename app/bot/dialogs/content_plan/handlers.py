from datetime import date
from typing import TYPE_CHECKING

from aiogram.types import CallbackQuery

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from app.bot.db.message_requests import cancel_post
from app.bot.states.manager.content import ContentSG
from taskiq_nats import NATSKeyValueScheduleSource

import logging

from app.bot.utils.enums.message import MessageType

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type: ignore

logger = logging.getLogger(__name__)


async def on_date_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, selected_date: date
):
    dialog_manager.dialog_data["selected_date"] = selected_date
    logger.debug(
        f"Пользователь {callback.from_user.id} выбрал {selected_date} для отображения запланированных постов."
    )
    recipient_type = dialog_manager.dialog_data.get("recipient_type")
    if recipient_type == MessageType.BOT.value:
        await dialog_manager.switch_to(ContentSG.today_info)
    elif recipient_type == MessageType.CHANNEL.value:
        await dialog_manager.switch_to(ContentSG.today_info)


async def type_selected(
    callback: CallbackQuery, _: Button, dialog_manager: DialogManager
):
    dialog_manager.dialog_data["recipient_type"] = callback.data


async def on_post_selected(
    callback: CallbackQuery, _: Button, dialog_manager: DialogManager, schedule_id: str
):
    dialog_manager.dialog_data["schedule_id"] = schedule_id
    await dialog_manager.switch_to(ContentSG.process_selected)


async def on_cancel_selected(
    callback: CallbackQuery, _: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session = dialog_manager.middleware_data.get("session")
    nats_source: NATSKeyValueScheduleSource = dialog_manager.middleware_data.get(
        "nats_source"
    )

    schedule_id = dialog_manager.dialog_data.get("schedule_id")

    try:
        await nats_source.delete_schedule(schedule_id)

        if await cancel_post(session=session, schedule_id=schedule_id):
            await callback.message.answer(i18n.content.successfull.deleted())
            logger.info(f"Запланированный пост {schedule_id} был успешно отменен.")
            dialog_manager.dialog_data["selected_date"] = None

            if (
                dialog_manager.dialog_data.get("recipient_type")
                == MessageType.BOT.value
            ):
                await dialog_manager.switch_to(ContentSG.bot)
            elif (
                dialog_manager.dialog_data.get("recipient_type")
                == MessageType.CHANNEL.value
            ):
                await dialog_manager.switch_to(ContentSG.channel)

        else:
            raise ValueError(f"Не удалось отменить пост {schedule_id}.")
    except Exception:
        await callback.message.answer(i18n.content.unsuccessful.deleted())
        logger.error("Произошла ошибка в обработке отмены поста.")
