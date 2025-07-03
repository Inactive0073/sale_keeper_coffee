class UserError(Exception):
    pass


class NotFoundError(UserError):
    """Если пользователь не был найден."""

    pass


class AlreadyHaveAllRoles(UserError):
    pass
