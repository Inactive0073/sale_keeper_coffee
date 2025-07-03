from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.common import sync_scroll
from aiogram_dialog.widgets.text import Format, List
from aiogram_dialog.widgets.kbd import (
    Button,
    Group,
    SwitchTo,
    Start,
    Select,
    ScrollingGroup,
    Multiselect,
)
from aiogram_dialog.widgets.input import TextInput

from app.bot.states.admin import AdminSG
from app.bot.states.customer.start import CustomerSG
from app.bot.states.manager.manager import ManagerSG
from app.bot.states.waiter.start import WaiterSG
from .handlers import (
    process_to_select_role,
    process_username_or_id,
    process_kick_button,
)
from .getters import (
    get_approve_data,
    get_ban_data,
    get_common_data,
    get_kicking_data,
    get_reports_data,
    get_roles_data,
    get_team_data,
)
from .filters import filter_message_to_find_username_or_id
from .services import parse_username_or_id_data, get_telegram_id


admin_dialog = Dialog(
    Window(
        Format("{hello_admin}"),
        SwitchTo(Format("{team_menu_btn}"), id="team_selected", state=AdminSG.team),
        # SwitchTo(
        #     Format("{reports_btn}"), id="reports_selected", state=AdminSG.reports
        # ),
        Group(
            Start(
                Format("{manager_role_btn}"),
                id="roles_selected",
                state=ManagerSG.start,
            ),
            Start(
                Format("{waiter_role_btn}"),
                id="waiter_selected",
                state=WaiterSG.start,
            ),
            Start(
                Format("{customer_role_btn}"),
                id="customer_selected",
                state=CustomerSG.menu,
            ),
            # пока в заморозке
            # SwitchTo(
            #     Format("{ban_menu_btn}"), id="ban_menu_selected", state=AdminSG.ban_menu
            # ),
            width=2,
        ),
        state=AdminSG.start,
    ),
    # Отчеты
    Window(
        Format("{reports_msg}"),
        Group(
            SwitchTo(
                Format("{reports_users}"),
                id="reports_users_selected",
                state=AdminSG.report_users,
            ),
            # заморожено
            # SwitchTo(
            #     Format("{reports_scheduled_posts}"),
            #     id="reports_scheduled_posts_selected",
            #     state=AdminSG.report_posts,
            # ),
            SwitchTo(
                Format("{reports_bonus_records}"),
                id="reports_bonus_records_selected",
                state=AdminSG.report_bonuses,
            ),
            width=2,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.start),
        state=AdminSG.reports,
        getter=get_reports_data,
    ),
    # Команда
    Window(
        Format("{team_msg}"),
        Group(
            SwitchTo(
                Format("{team_add_btn}"),
                id="add_selected",
                state=AdminSG.selecting_role,
            ),
            SwitchTo(
                Format("{team_kick_btn}"),
                id="kick_selected",
                state=AdminSG.selecting_employee,
            ),
            width=2,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.start),
        state=AdminSG.team,
        getter=get_team_data,
    ),
    # Управление доступом (пока на стопе)
    Window(
        Format("{ban_msg}"),
        Group(
            SwitchTo(Format("{ban_btn}"), id="ban_btn_selected", state=AdminSG.ban),
            SwitchTo(
                Format("{unban_btn}"), id="unban_btn_selected", state=AdminSG.unban
            ),
            width=2,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.start),
        state=AdminSG.ban_menu,
        getter=get_ban_data,
    ),
    # Выдача отчетов
    # Window(),
    # Управление командой
    # раздел добавления
    Window(
        Format("{team_select_msg}"),
        Group(
            Select(
                Format("{item[0]}"),
                id="selected_role",
                item_id_getter=lambda item: item[0],
                items="roles",
                on_click=process_to_select_role,
            ),
            width=2,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.team),
        state=AdminSG.selecting_role,
        getter=get_roles_data,
    ),
    Window(
        Format("{team_invite_msg}"),
        TextInput(
            id="processing_invite_new_member",
            type_factory=parse_username_or_id_data,
            on_success=process_username_or_id,
            filter=filter_message_to_find_username_or_id,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.team),
        state=AdminSG.invite,
        getter=get_team_data,
    ),
    # раздел удаления
    Window(
        Format("{team_kick_msg}"),
        List(
            Format(
                "{pos}. @{item.username} | {item.first_name} <b>ID:<code>{item.telegram_id}</code></b>"
            ),
            items="employees",
            id="list_employees",
            page_size=12,
        ),
        ScrollingGroup(
            Multiselect(
                Format("✓ {item.first_name} | {item.username}"),
                Format("{item.first_name} | {item.username}"),
                id="ms_employees",
                items="employees",
                item_id_getter=get_telegram_id,
            ),
            id="sg_employees",
            width=2,
            height=6,
            on_page_changed=sync_scroll("list_employees"),
            hide_on_single_page=True,
        ),
        SwitchTo(
            Format("{next}"),
            id="to_kick_employees",
            state=AdminSG.kick,
            when="selected_employees",
        ),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.team),
        state=AdminSG.selecting_employee,
        getter=get_kicking_data,
        preview_data=get_kicking_data,
    ),
    Window(
        Format("{approve_kick_msg}"),
        Button(Format("{yes}"), id="on_kick_selected", on_click=process_kick_button),
        SwitchTo(Format("{back}"), id="__back__", state=AdminSG.selecting_employee),
        state=AdminSG.kick,
        getter=get_approve_data,
    ),
    getter=get_common_data,
)
