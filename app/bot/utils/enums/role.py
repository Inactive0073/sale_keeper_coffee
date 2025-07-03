from enum import Enum


class UserType(str, Enum):
    WAITER = "waiter"
    MANAGER = "manager"
    ADMIN = "admin"
    OWNER = "owner"

    @classmethod
    def get_roles(cls, with_id: bool = False) -> list[str] | list[tuple[str, int]]:
        """Возвращает список ролей без роли владельца.

        Если указан with_id, то возвращается список кортежей, list[tuple[str, int]]
        """
        if not with_id:
            return [role.value for role in cls if role.value != cls.OWNER.value]
        else:
            return [
                (role.value, id_)
                for id_, role in enumerate(cls, start=1)
                if role.value != cls.OWNER.value
            ]
