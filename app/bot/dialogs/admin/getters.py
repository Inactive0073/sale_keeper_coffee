from typing import TYPE_CHECKING, Dict
from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Multiselect
from fluentogram import TranslatorRunner

from app.bot.db.admin_requests import get_employees
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
        "hello_admin": i18n.admin.hello.message(),
        "next": i18n.next(),
        "yes": i18n.yes(),
        "no": i18n.no(),
        "a_u_sure?": i18n.a.u.sure(),
        "reports_btn": i18n.admin.reports.btn(),
        "customer_role_btn": i18n.admin.role.customer.btn(),
        "waiter_role_btn": i18n.admin.role.waiter.btn(),
        "manager_role_btn": i18n.admin.role.manager.btn(),
        "ban_menu_btn": i18n.admin.ban.menu.btn(),
        "team_menu_btn": i18n.admin.team.btn(),
    }


async def get_reports_data(
    dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs
) -> Dict[str, str]:
    return {
        "reports_msg": i18n.admin.reports.menu.msg(),
        "reports_users": i18n.admin.reports.all_.users.btn(),
        "reports_scheduled_posts": i18n.admin.reports.all_.scheduled_posts.btn(),
        "reports_bonus_records": i18n.admin.reports.bonus.accrual.records.btn(),
    }


async def get_team_data(
    dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs
) -> Dict[str, str]:
    return {
        "team_msg": i18n.admin.team.menu.msg(),
        "team_add_btn": i18n.admin.team.invite.btn(),
        "team_invite_msg": i18n.admin.team.invite.msg(),
        "team_kick_btn": i18n.admin.team.kick.btn(),
    }


async def get_roles_data(
    dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs
) -> Dict[str, str]:
    roles = UserType.get_roles(with_id=True)
    return {"team_select_msg": i18n.admin.team.select.role.msg(), "roles": roles}


async def get_kicking_data(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    event_from_user: User,
    **kwargs,
) -> Dict[str, str]:
    session = dialog_manager.middleware_data.get("session")
    ms: Multiselect = dialog_manager.find("ms_employees")
    selected_employees = ms.get_checked()
    employees = []
    for user in await get_employees(session=session):
        user.username = "нет никнейма" if user.username is None else user.username
        if user.username != event_from_user.username:
            employees.append(user)

    return {
        "selected_employees": selected_employees,
        "team_kick_msg": i18n.admin.team.kick.msg(),
        "employees": employees,
    }


async def get_approve_data(
    dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs
) -> Dict[str, str]:
    return {"approve_kick_msg": i18n.admin.team.approve.kick.msg()}


async def get_ban_data(
    dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs
) -> Dict[str, str]:
    return {
        "ban_msg": i18n.admin.ban.menu.msg(),
        "ban_btn": i18n.admin.ban.menu.btn(),
        "unban_btn": i18n.admin.ban.menu.msg(),
        "not_found": i18n.admin.ban.not_.found.msg(),
    }
