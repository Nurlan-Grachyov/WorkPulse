from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_async_session
from app.main import fastapi_app
from app.models.db_user import User
from app.schemas.scheme_user import RoleCompany
from auth import current_superuser, current_active_user, hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def db_session(test_db):
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
async def app(db_session):
    async def override_get_async_db():
        yield db_session

    fastapi_app.dependency_overrides[get_async_session] = override_get_async_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def client(app, db_session):
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    if get_async_session in fastapi_app.dependency_overrides:
        del fastapi_app.dependency_overrides[get_async_session]


@pytest.fixture(scope="session")
async def admin_user(db_session: AsyncSession) -> User:
    result = await db_session.scalars(
        select(User).where(User.email == "admin@example.com")
    )
    admin = result.one_or_none()

    if admin is None:
        raw_password = "12345"
        hashed_password = hash_password(raw_password)
        admin = User(
            email="admin@example.com",
            hashed_password=hashed_password,
            role=RoleCompany.ADMIN,
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

    return admin


@pytest.fixture(scope="session")
async def usual_user(db_session: AsyncSession) -> User:
    result = await db_session.scalars(
        select(User).where(User.email == "user@example.com")
    )
    user = result.one_or_none()

    if user is None:
        raw_password = "12345"
        hashed_password = hash_password(raw_password)
        user = User(
            email="user@example.com",
            hashed_password=hashed_password,
            role=RoleCompany.USER,
            is_superuser=False,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

    return user


@pytest.fixture
def override_auth_admin(admin_user):
    fastapi_app.dependency_overrides[current_superuser] = lambda: admin_user
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def override_auth_user(usual_user):
    fastapi_app.dependency_overrides[current_active_user] = lambda: usual_user
    yield
    fastapi_app.dependency_overrides.clear()
