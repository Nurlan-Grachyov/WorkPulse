import asyncio

import bcrypt

import app.models.db_comment  # Comment
import app.models.db_evaluation  # Evaluation
import app.models.db_meeting  # Meeting
import app.models.db_task  # Task
import app.models.db_team  # Team
import app.models.db_user  # User  # noqa: F401
from app.database import async_session
from app.models.db_user import User
from app.schemas.scheme_user import Role


async def main():
    async with async_session() as session:
        raw_password = b"admin"
        hashed_password = bcrypt.hashpw(raw_password, bcrypt.gensalt()).decode("utf-8")
        print(f"✅ Хеш: {hashed_password[:20]}...")
        user = User(
            email="admin@example.com",
            hashed_password=hashed_password,
            role=Role.ADMIN,
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        print(f"✅ Админ создан: {user.email} (ID: {user.id})")


if __name__ == "__main__":
    asyncio.run(main())
