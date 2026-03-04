from src.application.schemas.scheme_user import UserUpdate
from src.domain.users.repositories import UserRepository
from src.domain.users.services import update_user_fields
from src.infrastructure.users.repositories import user_model_to_entity


class UserService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def get_users(self):
        return await self._users.get_users()

    async def get_user(self, slug):
        user = await self._users.get_user(slug)

        if user is None:
            raise LookupError("user_not_found")
        return user

    async def update_user(self, slug: str, data_for_update_user: dict):
        user = await self._users.get_user(slug)
        if user is None:
            raise LookupError("user_not_found")

        updated_user = update_user_fields(user, data_for_update_user)

        return await self._users.update_user(updated_user)

    async def delete_user(self, slug: str) -> None:
        user = await self._users.get_user(slug)
        if user is None:
            raise LookupError("user_not_found")
        await self._users.delete_user(user)
