from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

import app.models.db_comment  # noqa:  F401
import app.models.db_evaluation  # noqa:  F401
import app.models.db_meeting  # noqa:  F401
import app.models.db_task  # noqa:  F401
import app.models.db_team  # noqa:  F401
from app import admin  # noqa:  F401
from app.database import async_session
from app.models.db_user import User  # User
from app.routers.calendar import calendar_router
from app.routers.comment import comment_router
from app.routers.evaluation import evaluation_router
from app.routers.meeting import meeting_router
from app.routers.task import task_router
from app.routers.team import team_router
from app.routers.user import user_router
from app.schemas.scheme_user import RoleCompany, UserCreate, UserRead, UserUpdate
from auth import auth_backend, fastapi_users, hash_password


@asynccontextmanager
async def lifespan(lifespan_app: FastAPI):
    # Create ADMIN if there is no admin yet
    async with async_session() as session:
        exists_admin = session.scalar(
            select(User).where(User.role == RoleCompany.ADMIN)
        )
        if not exists_admin:
            raw_password = "12345"
            hashed_password = hash_password(raw_password)

            print(f"✅ Хеш: {hashed_password[:20]}...")
            user = User(
                email="admin@example.com",
                hashed_password=hashed_password,
                role=RoleCompany.ADMIN,
                is_superuser=True,
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.commit()
            print(f"✅ Админ создан: {user.email} (ID: {user.id})")
        else:
            pass

    yield


def create_app():
    fastapi_app = FastAPI(title="WorkPulse", detail="Welcome", lifespan=lifespan)

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # порт фронта
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fastapi_app.include_router(
        fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
    )
    fastapi_app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["auth"],
    )
    fastapi_app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/auth",
        tags=["auth"],
    )
    fastapi_app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/auth",
        tags=["auth"],
    )
    fastapi_app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["fastapi-users"],
    )

    fastapi_app.include_router(user_router)
    fastapi_app.include_router(team_router)
    fastapi_app.include_router(task_router)
    fastapi_app.include_router(comment_router)
    fastapi_app.include_router(evaluation_router)
    fastapi_app.include_router(meeting_router)
    fastapi_app.include_router(calendar_router)

    from app.admin import init_admin

    init_admin(fastapi_app)

    return fastapi_app


fastapi_app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:fastapi_app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True,
    )
