from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Group, Start
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory

from app.bot.dialogs.manager.getters import get_hello
from app.bot.states.admin.admin import AdminSG
from app.bot.states.manager.manager import ManagerSG
from app.bot.states.manager.addition_channel import AdditionToChannelSG
from app.bot.states.manager.creating_post import PostingSG
from app.bot.states.manager.settings import SettingsSG
from app.bot.states.manager.content import ContentSG


manager_dialog = Dialog(
    Window(
        Format("{hello_admin}"),
        Group(
            Start(
                text=Format("{create_post}"),
                id="create_post_pressed",
                state=PostingSG.select_channels,
                show_mode=ShowMode.DELETE_AND_SEND,
            ),
            Start(Format("{my_posts}"), id="my_posts_pressed", state=ContentSG.start),
            # Button(Format("{create_description}"), id="create_descript_card_pressed"), # пока отложено
            Start(
                text=Format("{settings}"),
                id="settings_pressed",
                state=SettingsSG.start,
                show_mode=ShowMode.DELETE_AND_SEND,
            ),
            Start(
                text=Format("{add_channel}"),
                id="add_channel_pressed",
                state=AdditionToChannelSG.start,
                show_mode=ShowMode.DELETE_AND_SEND,
            ),
            width=2,
        ),
        Start(
            Format("{to_admin_menu}"),
            id="to_admin_menu",
            state=AdminSG.start,
            when="is_admin",
        ),
        getter=get_hello,
        state=ManagerSG.start,
        markup_factory=ReplyKeyboardFactory(
            resize_keyboard=True,
            input_field_placeholder=Const("Выберите пункт меню"),
            # one_time_keyboard=True
        ),
    )
)
