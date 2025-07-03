from datetime import datetime, timedelta, timezone, UTC
from typing import TYPE_CHECKING, Dict

from aiogram.types import User

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import ManagedRadio

from fluentogram import TranslatorRunner

from app.bot.db.common_requests import get_user_role
from app.bot.db.manager_requests import get_user_tz
from app.bot.utils.enums.role import UserType

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type:ignore


TIMEZONES = [
    ("Калининград", "Europe/Kaliningrad", 2),
    ("Москва", "Europe/Moscow", 3),
    ("Самара", "Europe/Samara", 4),
    ("Екатеринбург", "Asia/Yekaterinburg", 5),
    ("Омск", "Asia/Omsk", 6),
    ("Красноярск", "Asia/Krasnoyarsk", 7),
    ("Иркутск", "Asia/Irkutsk", 8),
    ("Якутск", "Asia/Yakutsk", 9),
    ("Владивосток", "Asia/Vladivostok", 10),
    ("Магадан", "Asia/Magadan", 11),
    ("Камчатка", "Asia/Kamchatka", 12),
]


async def get_settings_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "cancel_caption": i18n.cancel(),
        "yes_caption": i18n.yes(),
        "next": i18n.next(),
        "back": i18n.back(),
        "settings_support_message": i18n.settings.support.message(),
    }


async def get_setting_menu_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    is_admin = UserType.ADMIN in await get_user_role(
        session=session, telegram_id=event_from_user.id
    )
    return {
        "settings_menu_message": i18n.settings.main.menu(),
        "settings_timezone_button": i18n.settings.timezone.button(),
        "settings_support_button": i18n.settings.support.button(),
        "is_admin": is_admin,
    }


async def get_start_setting_tz_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    user_timezone, tz_offset = await get_user_tz(
        session=session, telegram_id=event_from_user.id
    )
    user_time = datetime.now(tz=timezone(timedelta(hours=tz_offset))).strftime(
        "%d.%m | %H:%M"
    )
    utc_time: datetime = datetime.now(tz=UTC)

    radio: ManagedRadio = dialog_manager.find("selecting_timezones")
    await radio.set_checked(f"{user_timezone}|{tz_offset}")

    tz_buttons = []
    for name, tz_label, offset in TIMEZONES:
        dt = utc_time + (timedelta(hours=offset))
        dt_formatted = dt.strftime("%d.%m | %H:%M")
        tz_buttons.append((f"{name} {dt_formatted}", f"{tz_label}|{offset}"))

    return {
        "settings_select_timezone_message": i18n.settings.select.timezone(
            current_timezone=user_timezone, local_datetime=user_time
        ),
        "timezones": tz_buttons,
    }
