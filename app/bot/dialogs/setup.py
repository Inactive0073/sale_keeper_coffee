from typing import List
from aiogram_dialog import Dialog

from .admin.dialogs import admin_dialog
from .manager.dialogs import manager_dialog
from .creating_post.dialogs import create_post_dialog
from .addition_channel.dialogs import dialog_addition_channel
from .settings.dialogs import settings_dialog
from .customer_user.dialogs import customer_dialog
from .waiter.dialogs import waiter_dialog
from .content_plan.dialogs import content_dialog


def get_dialogs() -> List[Dialog]:
    return [
        admin_dialog,
        manager_dialog,
        create_post_dialog,
        dialog_addition_channel,
        settings_dialog,
        customer_dialog,
        waiter_dialog,
        content_dialog,
    ]
