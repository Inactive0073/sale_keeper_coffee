from typing import TYPE_CHECKING, Dict

from aiogram.types import User, ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from fluentogram import TranslatorRunner

from app.bot.db.common_requests import get_user_role
from app.bot.paths import WAITER_MEDIA_DIR
from app.bot.utils.enums.role import UserType
from .constants import ID_STUB_SCROLL


if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type:ignore


async def get_common_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    web_app_url = dialog_manager.middleware_data.get("web_app_url")
    session = dialog_manager.middleware_data.get("session")
    is_admin = UserType.ADMIN in await get_user_role(
        session=session, telegram_id=event_from_user.id
    )
    return {
        "back": i18n.back(),
        "hello_waiter": i18n.waiter.hello.message(),
        "waiter_menu_scan": i18n.waiter.menu.scan(),
        "waiter_menu_scan_url": f"{web_app_url}/scan",
        "is_admin": is_admin,
        "to_admin_menu": i18n.admin.comeback.btn(),
    }


async def paging_getter(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    # +1 поскольку вернет индекс
    current_page = await dialog_manager.find(ID_STUB_SCROLL).get_page() + 1
    photo = MediaAttachment(
        type=ContentType.PHOTO, path=f"{WAITER_MEDIA_DIR}/{current_page}.png"
    )

    # Динамическое обращение к demo.instruction.message._N
    instruction_attr = str(current_page)
    instruction_message = getattr(i18n.waiter.instruction.message, instruction_attr)()
    count_photos = len(
        [p for p in WAITER_MEDIA_DIR.iterdir() if p.is_file() and p.suffix == ".png"]
    )
    return {
        "back": i18n.back(),
        "pages": count_photos,
        "pagination_message": i18n.waiter.pagination.message(
            current_page=current_page, pages=count_photos
        ),
        "instruction_message": instruction_message,
        "current_page": current_page,
        "media_file": photo,
    }


async def get_processing_guest_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> Dict[str, str]:
    return {
        "process_guest_message": i18n.waiter.processing.instruction(),
        "add_bonus_button": i18n.waiter.processing.add.bonus(),
        "subtract_bonus_button": i18n.waiter.processing.subtract.bonus(),
        "adding_instruction": i18n.waiter.processing.adding.bonus.instruction(),
        "subtracting_instruction": i18n.waiter.processing.subtracting.instruction(),
    }
