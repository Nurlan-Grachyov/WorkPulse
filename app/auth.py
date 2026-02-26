import os
import uuid

from dotenv import load_dotenv
from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_async_session
from app.models.db_user import User
from app.schemas.scheme_user import RoleTeam

load_dotenv()
SECRET = os.getenv("SECRET_KEY")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)  # type: ignore[arg-type]


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def has_manager_rights(user_id: uuid.UUID, db: AsyncSession) -> bool:
    """
    Check if user has manager role in their team.

    Args:
        user_id: User UUID identifier
        db: Async SQLAlchemy session

    Returns:
        True if user has TeamUser link with MANAGER role, False otherwise

    Notes:
        - Returns False for users without team (team_link is None)
        - Uses direct select(User.team_link) without joinedload for performance
        - one_or_none() safely handles missing/duplicate links
    """
    result = await db.scalars(
        select(User).options(joinedload(User.team_link)).where(User.id == user_id)
    )
    user = result.one_or_none()

    return user.team_link is not None and user.team_link.role == RoleTeam.MANAGER


pwd_context = CryptContext(
    schemes=[
        "argon2",
        "bcrypt",
        "pbkdf2_sha256",
    ],
    default="argon2",
    argon2__default_rounds=10,
)


def hash_password(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли введённый пароль сохранённому хешу.
    """
    return pwd_context.verify(plain_password, hashed_password)
