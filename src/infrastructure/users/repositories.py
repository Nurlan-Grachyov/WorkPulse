from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.users.entities import User
from src.infrastructure.db.models.db_user import User as UserModel


def user_model_to_entity(user: UserModel) -> User:
    return User(
        id=user.id,
        email=user.email,
        slug=user.slug,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
        role=user.role,
        is_verified=user.is_verified,
    )


def user_entity_to_model(entity: User, model: UserModel | None = None) -> UserModel:
    if model is None:
        model = UserModel()
    model.email = entity.email
    model.slug = entity.slug
    model.hashed_password = entity.hashed_password
    model.is_active = entity.is_active
    model.role = entity.role
    model.is_verified = entity.is_verified
    return model


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_users(self):
        users = await self._session.scalars(
            select(UserModel).where(UserModel.is_active)
        )
        db_users = users.all()
        return db_users

    async def get_user(self, slug: str = None, email: str = None):
        db_user = None

        if slug:
            user = await self._session.scalars(
                select(UserModel).where(UserModel.slug == slug)
            )
            db_user = user.one_or_none()
        elif email:
            user = await self._session.scalars(
                select(UserModel).where(UserModel.email == email)
            )
            db_user = user.one_or_none()

        if db_user is None:
            raise LookupError("user_not_found")
        return db_user

    async def get_user_with_team_link(self, slug: str = None, email: str = None):
        db_user = None

        if slug:
            user = await self._session.scalars(
                select(UserModel)
                .options(joinedload(UserModel.team_link))
                .where(UserModel.slug == slug)
            )
            db_user = user.one_or_none()
        elif email:
            user = await self._session.scalars(
                select(UserModel)
                .options(joinedload(UserModel.team_link))
                .where(UserModel.email == email)
            )
            db_user = user.one_or_none()

        if db_user is None:
            raise LookupError("user_not_found")
        return db_user

    async def update_user(self, user: User):
        result = await self._session.scalars(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.one_or_none()
        if model is None:
            raise LookupError("user_not_found")
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def delete_user(self, user: User):
        result_user = await self._session.scalars(
            select(UserModel).where(UserModel.id == user.id)
        )
        db_user = result_user.one_or_none()
        if db_user is None:
            raise LookupError("user_not_found")
        await self._session.delete(db_user)
        await self._session.commit()
