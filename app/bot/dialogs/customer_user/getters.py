from typing import TYPE_CHECKING, Dict
from aiogram.types import User
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner

from app.bot.db.common_requests import get_user_role
from app.bot.utils.enums import UserType

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type:ignore


async def get_common_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "back": i18n.back(),
        "hello_guest": i18n.customer.hello.message(),
        "meeting_phone_message": i18n.customer.meeting.phone(),
        "meeting_name_message": i18n.customer.meeting.name(),
        "meeting_surname_message": i18n.customer.meeting.surname(),
        "meeting_email_message": i18n.customer.meeting.email(),
        "meeting_birthday_message": i18n.customer.meeting.birthday(),
        "meeting_gender_message": i18n.customer.meeting.gender(),
        "meeting_gender_m_button": i18n.customer.meeting.gender.m(),
        "meeting_gender_f_button": i18n.customer.meeting.gender.f(),
        "meeting_thanks_message": i18n.customer.meeting.thanks(),
    }


async def get_customer_menu_data(
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
        "menu_info_message": i18n.customer.menu.info.message(),
        "customer_menu_placeholder": i18n.customer.menu.placeholder(),
        "menu_balance_button": i18n.customer.menu.balance.button(),
        "menu_about_button": i18n.customer.menu.about.button(),
        "menu_card_button": i18n.customer.menu.card.button(),
        "menu_gifts_button": i18n.customer.menu.gifts.button(),
        "menu_menu_button": i18n.customer.about.message.menu(),
        "menu_delivery_button": i18n.customer.menu.delivery.button(),
        "menu_loayalty_button": i18n.customer.menu.loyalty.button(),
        "menu_partnership_button": i18n.customer.menu.partnership.button(),
        "menu_help_button": i18n.customer.menu.help.button(),
        "is_admin": is_admin,
        "to_admin_menu": i18n.admin.comeback.btn(),
    }
