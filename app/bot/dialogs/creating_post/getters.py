import datetime as dt

from typing import TYPE_CHECKING, Dict

from aiogram.types import User

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Multiselect

from dataclasses import dataclass

from fluentogram import TranslatorRunner

from app.bot.db.common_requests import get_user_role
from app.bot.db.manager_requests import get_channels, get_user_tz
from app.bot.utils.enums.role import UserType

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type:ignore


@dataclass
class BaseToggleItem:
    id: str
    desc: str


@dataclass
class NotifyAlert(BaseToggleItem): ...


@dataclass
class Spoiler(BaseToggleItem): ...


async def get_posting_sg_common_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "cancel_caption": i18n.cancel(),
        "yes_caption": i18n.yes(),
        "next": i18n.next(),
        "back": i18n.back(),
        "autocaption": i18n.caption(),
    }


async def get_watch_text(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "watch_text": i18n.cr.watch.text(),
    }


async def get_creating_post_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    content_msg = dialog_manager.dialog_data.get("post_message", "Сообщение не найдено")
    url_button_empty = dialog_manager.dialog_data.get("url_button_empty", True)

    posting_time = dialog_manager.dialog_data.get("dt_posting_view", None)
    posting_time_index = bool(posting_time)
    has_media = dialog_manager.dialog_data.get("has_media", False)
    has_keyboard = dialog_manager.dialog_data.get("has_keyboard", False)
    disable_notification = dialog_manager.dialog_data.get("disable_notification", True)
    has_spoiler = dialog_manager.dialog_data.get("has_spoiler", None)

    return {
        "reply_title": i18n.cr.reply.text(),
        "post_message": content_msg,
        "edit": i18n.cr.edit.text(),
        "url": i18n.cr.url.btns(),
        "url_delete": i18n.cr.url.delete(),
        "set_time": i18n.cr.set.time(),
        "posting_time": posting_time,
        "posting_time_index": posting_time_index,
        "states_notify": [
            NotifyAlert(id="enable_notification", desc=i18n.cr.set.notify()),
            NotifyAlert(id="disable_notification", desc=i18n.cr.unset.notify()),
        ],
        "states_spoiler": [
            Spoiler(id="hasnt_spoiler", desc=i18n.cr.unset.spoiler()),
            Spoiler(id="has_spoiler", desc=i18n.cr.set.spoiler()),
        ],
        "disable_notification": disable_notification,
        "media_message": i18n.cr.add.media(),
        "delete_media_message": i18n.cr.remove.media(),
        "has_media": has_media,
        "has_keyboard": has_keyboard,
        "unset_comments": i18n.cr.unset.comments(),
        "push_now": i18n.cr.push.now(),
        "push_later": i18n.cr.push.later(),
        "url_button_empty": url_button_empty,
        "url_button_exists": not url_button_empty,
    }


async def get_url_instruction(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "instruction_url": i18n.cr.instruction.url(),
    }


async def get_time_instruction_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    tz, tz_offset = await get_user_tz(session=session, telegram_id=event_from_user.id)
    return {"instruction_delayed_post": i18n.cr.instruction.delayed.post(tz=tz)}


async def get_addition_media_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "instruction_add_media": i18n.cr.instruction.media.post(),
    }


async def get_approve_push_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "push_now_approve_message": i18n.cr.approve.media.push.now(),
    }


async def get_preselect_channel_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    telegram_id = event_from_user.id
    channels = await get_channels(session=session, telegram_id=telegram_id)
    multiselect: Multiselect = dialog_manager.find("selected_channel_for_publication")
    one_or_more_selected = multiselect.get_checked()
    selected_channels = [
        (channel[2], channel[1])
        for channel in channels
        if channel[2] in one_or_more_selected
    ]
    is_admin = UserType.ADMIN in await get_user_role(
        session=session, telegram_id=event_from_user.id
    )

    dialog_manager.dialog_data["selected_channels"] = selected_channels
    return {
        "all_channels": channels,
        "mail_to_bots_subscribers_message": i18n.cr.select.bot.to.send.message(),
        "select_channel_message": i18n.cr.select.channel.to.send.message(),
        "one_or_more_selected": one_or_more_selected,
        "is_admin": is_admin,
    }


async def get_report_after_push_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    post_message = dialog_manager.dialog_data.get("post_message")
    date_posting = (
        dt.datetime.now().strftime("%d/%m, %H:%M")
        if (schedule_time := dialog_manager.dialog_data.get("dt_posting_view")) is None
        else schedule_time
    )
    report = i18n.cr.success.pushed.channel(
        post_message=post_message, date_posting=date_posting
    )
    channels_name = [
        channel for channel in dialog_manager.dialog_data.get("selected_channels", [])
    ]
    return {
        "report_message": report,
        "channels": channels_name,
        "main_menu": i18n.main.menu(),
        "edit_post_btn": i18n.cr.edit.scheduled.post.btn(),
    }


async def get_push_later_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    date_posting = dialog_manager.dialog_data["dt_posting_view"]
    selected_channels = dialog_manager.dialog_data["selected_channels"]
    return {
        "schedule_message": i18n.cr.push.later.message(current_date=date_posting),
        "selected_channels": selected_channels,
        "schedule_button_caption": i18n.cr.push.later.button.caption(),
    }


async def get_report_after_sending_subscribers(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    post_message = dialog_manager.dialog_data.get("post_message")
    count_acc = dialog_manager.dialog_data.get("count_acc_to_send")
    date_posting = (
        dt.datetime.now().strftime("%d/%m, %H:%M")
        if (schedule_time := dialog_manager.dialog_data.get("dt_posting_view")) is None
        else schedule_time
    )
    report_message = i18n.cr.success.send.bot.subscribers(
        post_message=post_message,
        date_posting=date_posting,
        count_people=count_acc,
        count_user=count_acc,
    )
    return {
        "report_message": report_message,
        "main_menu": i18n.main.menu(),
        "edit_post_btn": i18n.cr.edit.scheduled.post.btn(),
    }
