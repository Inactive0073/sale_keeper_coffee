import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, ShowMode, StartMode

from sqlalchemy.ext.asyncio import AsyncSession


from ..db.customer_requests import get_customer_detail_info, upsert_customer
from ..states.admin import AdminSG
from ..states.customer.start import CustomerSG
from ..states.manager.manager import ManagerSG
from ..states.waiter.start import WaiterSG
from ..db.common_requests import get_user_role

commands_router = Router(name=__name__)

logger = logging.getLogger(__name__)


@commands_router.message(CommandStart())
async def process_start_command(
    message: Message,
    dialog_manager: DialogManager,
    session: AsyncSession,
) -> None:
    username = message.from_user.username
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    roles = set(await get_user_role(session=session, telegram_id=telegram_id))
    logger.info(
        f"Пользователь {first_name}|{username} с ролями {roles}, нажал кнопку /start"
    )
    if not roles.intersection({"admin", "manager", "waiter", "owner"}):
        if not (await get_customer_detail_info(session, telegram_id)):
            logger.debug(f"Проверка {telegram_id} пройдена успешно!")
            await upsert_customer(
                session=session,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            logger.debug(f"Обновление данных {telegram_id} пройдено успешно")
            await dialog_manager.start(
                state=CustomerSG.start, mode=StartMode.RESET_STACK
            )
        else:
            await dialog_manager.start(
                state=CustomerSG.menu, show_mode=ShowMode.DELETE_AND_SEND
            )
    else:
        if "admin" in roles:
            await dialog_manager.start(state=AdminSG.start, mode=StartMode.RESET_STACK)
        elif "manager" in roles:
            await dialog_manager.start(
                state=ManagerSG.start, mode=StartMode.RESET_STACK
            )
        elif "waiter" in roles:
            await dialog_manager.start(state=WaiterSG.start, mode=StartMode.RESET_STACK)
