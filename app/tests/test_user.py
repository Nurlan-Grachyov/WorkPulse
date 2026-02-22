import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import fastapi_app
from app.models.db_user import User
from app.schemas.scheme_user import RoleCompany


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    user_data = {"email": "usual_user@example.com", "password": "testpass123"}
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "usual_user@example.com"


@pytest.mark.asyncio
async def test_register_admin(db_session, admin_user):
    db_session.add(admin_user)
    await db_session.commit()

    result = await db_session.scalars(
        select(User).where(User.email == "admin@example.com")
    )
    admin = result.one_or_none()
    assert admin is not None


@pytest.mark.asyncio
async def test_get_users(
        db_session: AsyncSession, client: AsyncClient, override_auth_user
):
    # print(f"{id(db_session)} test_get_users")
    result_user = await db_session.scalars(
        select(User).where(User.email == "user1@test.com")
    )
    db_user = result_user.one_or_none()
    try:
        if not db_user:
            test_user = User(
                email="user1@test.com", is_active=True, hashed_password="hash"
            )
            db_session.add(test_user)
            await db_session.commit()

        response = await client.get("/users/all_users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        emails = [u["email"] for u in users]
        assert "admin@example.com" in emails
        assert "user1@test.com" in emails

    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_user(db_session, client, override_auth_admin):
    # print(f"{id(db_session)} test_get_user")
    result_user = await db_session.scalars(
        select(User).where(User.email == "user1@test.com")
    )
    db_user = result_user.one_or_none()
    try:
        if not db_user:
            test_user = User(
                email="user1@test.com", is_active=True, hashed_password="hash"
            )
            db_session.add(test_user)
            await db_session.commit()

        update_user_data = {"role": RoleCompany.MANAGER}
        response = await client.patch("/users/user1@test.com/", json=update_user_data)
        assert response.status_code == 200
        user = response.json()
        assert user.get("email") == "user1@test.com"
        assert user.get("role") == RoleCompany.MANAGER

    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_user(db_session, client, override_auth_admin):
    result_user = await db_session.scalars(
        select(User).where(User.email == "user1@test.com")
    )
    db_user = result_user.one_or_none()
    try:
        if not db_user:
            test_user = User(
                email="user1@test.com", is_active=True, hashed_password="hash"
            )
            db_session.add(test_user)
            await db_session.commit()

        response = await client.delete("/users/user1@test.com/")
        assert response.status_code == 204
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_user_not_found(client, override_auth_admin):
    response = await client.patch("/users/nonexistent@test.com/", json={"role": RoleCompany.MANAGER})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_superadmin_forbidden(db_session, client, override_auth_admin):
    admin = User(email="super@test.com", role=RoleCompany.ADMIN, is_active=True, hashed_password="hash",
                 is_superuser=True)
    db_session.add(admin)
    await db_session.commit()

    response = await client.delete("/users/super@test.com/")
    assert response.status_code == 403
