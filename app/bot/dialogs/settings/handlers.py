from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.bot.db.manager_requests import set_user_tz


async def on_timezone_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    timezone_data: str,
):
    timezone, tz_offset = timezone_data.split("|")
    tz_offset = int(tz_offset)
    session = dialog_manager.middleware_data.get("session")
    dialog_manager.dialog_data["user_timezone"] = timezone_data
    dialog_manager.dialog_data["tz_offset"] = tz_offset
    await set_user_tz(
        session=session,
        telegram_id=callback.from_user.id,
        tz_offset=tz_offset,
        timezone=timezone,
    )
