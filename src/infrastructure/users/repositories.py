from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        try:
            users = await self._session.scalars(
                select(UserModel).where(UserModel.is_active)
            )
            db_users = users.all()
        except Exception as exc:
            raise RuntimeError("DB error while fetching users") from exc
        return [user_model_to_entity(user) for user in db_users]

    async def get_user(self, slug: str):
        user = await self._session.scalars(
            select(UserModel).where(UserModel.slug == slug)
        )
        db_user = user.one_or_none()
        return user_model_to_entity(db_user)

    async def update_user(self, user: User):
        result = await self._session.scalars(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.one()
        model = user_entity_to_model(user, model=model)
        await self._session.commit()
        await self._session.refresh(model)
        return user_model_to_entity(model)

    async def delete_user(self, user: User):
        result_user = await self._session.scalars(
            select(UserModel).where(UserModel.id == user.id)
        )
        db_user = result_user.one_or_none()
        if db_user is None:
            raise LookupError("user_not_found")
        await self._session.delete(db_user)
        await self._session.commit()
