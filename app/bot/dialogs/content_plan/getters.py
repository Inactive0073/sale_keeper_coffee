from typing import TYPE_CHECKING, Dict

from aiogram.types import User

from aiogram_dialog import DialogManager
from app.bot.db.manager_requests import get_user_tz

from fluentogram import TranslatorRunner

from datetime import timedelta, datetime, timezone, date

from app.bot.db.message_requests import get_posts
from app.bot.utils.enums import MessageType
from app.bot.utils.schemas.models import PostData
from .services import find_selected_posts, parse_post_data


if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type:ignore

months = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


async def content_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "main_menu": i18n.main.menu(),
        "content_hello_msg": i18n.content.hello(),
        "content_bot_btn": i18n.content.bot.btn(),
        "content_channel_btn": i18n.content.channel.btn(),
        "to_cancel": i18n.to.cancel(),
        "edit_btn": i18n.edit(),
        "back": i18n.back(),
        "process_selected_post_msg": i18n.content.process.select.post.msg(),
    }


async def content_posts_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    recipient_type = dialog_manager.dialog_data.get("recipient_type")
    if recipient_type == MessageType.BOT.value:
        all_posts = await get_posts(session=session, target_type=MessageType.BOT)
    else:
        all_posts = await get_posts(session=session, target_type=MessageType.CHANNEL)

    _, user_tz_offset = await get_user_tz(
        session=session, telegram_id=event_from_user.id
    )
    user_tz = timezone(timedelta(hours=user_tz_offset))
    idx_month = datetime.now(tz=user_tz).month
    current_month = months[idx_month]
    parsed_data = parse_post_data(all_posts, tzinfo=user_tz)
    days_with_posts = [post.scheduled_time.date() for post in all_posts]

    dialog_manager.dialog_data["days_with_posts"] = days_with_posts
    dialog_manager.dialog_data["user_tz_offset"] = user_tz_offset
    dialog_manager.dialog_data["parsed_posts"] = parsed_data

    text_month_info = i18n.content.month.info.msg(
        month=current_month, type_=recipient_type, count_post=len(parsed_data)
    )

    return {
        "content_msg": text_month_info,
    }


async def content_today_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    user_tz_offset = dialog_manager.dialog_data.get("user_tz_offset")
    recipient_type = dialog_manager.dialog_data.get("recipient_type")
    selected_date = dialog_manager.dialog_data.get("selected_date")
    if type(selected_date) == str:
        year, month, day = map(
            int, dialog_manager.dialog_data.get("selected_date").split("-")
        )  # Данные приходят в формате yyyy-mm-dd
        selected_date = date(year, month, day)

    selected_datetime = datetime.fromisoformat(selected_date.isoformat()).replace(
        tzinfo=timezone(timedelta(hours=user_tz_offset))
    )
    parsed_posts = [
        PostData.model_validate(post)
        for post in dialog_manager.dialog_data.get("parsed_posts")
    ]
    today_posts = find_selected_posts(parsed_posts, selected_datetime)
    count_posts = len(today_posts)

    text_today_info = i18n.content.today.info.msg(
        selected_date=selected_date.strftime("%d.%m"),
        type_=recipient_type,
        count_post=count_posts,
    )
    return {
        "today_info_msg": text_today_info,
        "posts": today_posts,
    }
