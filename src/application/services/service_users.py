from src.domain.users.repositories import UserRepository
from src.domain.users.services import update_user_fields


class UserService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def get_users(self):
        return await self._users.get_users()

    async def get_user(self, slug: str = None, email: str = None):
        user = None

        if slug:
            user = await self._users.get_user(slug=slug)
        elif email:
            user = await self._users.get_user(email=email)

        if user is None:
            raise LookupError("user_not_found")
        return user

    async def get_user_with_team_link(self, slug: str = None, email: str = None):
        user = None

        if slug:
            user = await self._users.get_user_with_team_link(slug=slug)
        elif email:
            user = await self._users.get_user_with_team_link(email=email)

        if user is None:
            raise LookupError("user_not_found")
        return user

    async def update_user(self, email: str, data_for_update_user: dict):
        user = await self._users.get_user(email=email)
        if user is None:
            raise LookupError("user_not_found")

        updated_user = update_user_fields(user, data_for_update_user)

        return await self._users.update_user(updated_user)

    async def delete_user(self, slug: str) -> None:
        user = await self._users.get_user(slug=slug)
        if user is None:
            raise LookupError("user_not_found")
        await self._users.delete_user(user)
