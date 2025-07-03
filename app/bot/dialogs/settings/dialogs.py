from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Group, SwitchTo, Radio, Start, Column

from app.bot.states.manager.manager import ManagerSG
from app.bot.states.manager.settings import SettingsSG
from .getters import get_setting_menu_data, get_settings_data, get_start_setting_tz_data
from .handlers import on_timezone_selected

settings_dialog = Dialog(
    Window(
        Format("{settings_menu_message}"),
        Group(
            SwitchTo(
                Format("{settings_timezone_button}"),
                id="timezone_selected",
                state=SettingsSG.timezone,
            ),
            SwitchTo(
                Format("{settings_support_button}"),
                id="support_selected",
                state=SettingsSG.support,
            ),
            width=2,
        ),
        Start(
            Format("{back}"), id="back_to_menu", state=ManagerSG.start, when="is_admin"
        ),
        state=SettingsSG.start,
        getter=get_setting_menu_data,
    ),
    # Окно настройки часового пояса
    Window(
        Format("{settings_select_timezone_message}"),
        Column(
            Radio(
                Format("✅ {item[0]}"),
                Format("{item[0]}"),
                id="selecting_timezones",
                item_id_getter=lambda item: item[1],
                items="timezones",
                on_click=on_timezone_selected,
            ),
        ),
        SwitchTo(Format("{back}"), id="__back__", state=SettingsSG.start),
        state=SettingsSG.timezone,
        getter=get_start_setting_tz_data,
    ),
    # Окно поддержки
    Window(
        Format("{settings_support_message}"),
        SwitchTo(Format("{back}"), id="__back__", state=SettingsSG.start),
        state=SettingsSG.support,
    ),
    getter=get_settings_data,
)
