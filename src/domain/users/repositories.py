from typing import Protocol

from src.domain.users.entities import User


class UserRepository(Protocol):
    async def get_users(self) -> list[User]: ...

    async def get_user(self, slug: str = None, email: str = None) -> User | None: ...

    async def update_user(self, user: User) -> User: ...

    async def delete_user(self, user: User) -> None: ...

    async def get_user_with_team_link(
        self, slug: str = None, email: str = None
    ) -> User | None: ...
