from src.domain.users.entities import User


def update_user_fields(user: User, fields) -> User:
    for field, value in fields.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)
    return user
