from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

import app.models.db_comment  # noqa:  F401
import app.models.db_evaluation  # noqa:  F401
import app.models.db_meeting  # noqa:  F401
import app.models.db_task  # noqa:  F401
import app.models.db_team  # noqa:  F401
from app import admin  # noqa:  F401
from app.admin import init_admin
from app.auth import auth_backend, fastapi_users, hash_password
from app.database import async_session
from app.models.db_user import User
from app.routers.calendar import calendar_router
from app.routers.comment import comment_router
from app.routers.evaluation import evaluation_router
from app.routers.meeting import meeting_router
from app.routers.task import task_router
from app.routers.team import team_router
from app.routers.user import user_router
from app.schemas.scheme_user import RoleCompany, UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(lifespan_app: FastAPI):
    async with async_session() as session:
        result_exists_admin = await session.scalars(
            select(User).where(User.role == RoleCompany.ADMIN)
        )
        exists_admin = result_exists_admin.one_or_none()
        if not exists_admin:
            raw_password = "admin"
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
            await session.refresh(user)
            print(f"✅ Админ создан: {user.email} (ID: {user.id})")

    yield


def create_app() -> FastAPI:
    fastapi_app = FastAPI(title="WorkPulse", detail="Welcome", lifespan=lifespan)
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"

    # static и templates внутри app/
    fastapi_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # AUTH (fastapi-users)
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

    # HTML страницы
    @fastapi_app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @fastapi_app.get("/users", response_class=HTMLResponse)
    async def users_page(request: Request):
        return templates.TemplateResponse("users.html", {"request": request})

    @fastapi_app.get("/teams", response_class=HTMLResponse)
    async def teams_page(request: Request):
        return templates.TemplateResponse("teams.html", {"request": request})

    @fastapi_app.get("/tasks", response_class=HTMLResponse)
    async def tasks_page(request: Request):
        return templates.TemplateResponse("tasks.html", {"request": request})

    @fastapi_app.get("/evaluations", response_class=HTMLResponse)
    async def evaluations_page(request: Request):
        return templates.TemplateResponse("evaluations.html", {"request": request})

    @fastapi_app.get("/comments", response_class=HTMLResponse)
    async def comments_page(request: Request):
        return templates.TemplateResponse("comments.html", {"request": request})

    @fastapi_app.get("/meetings", response_class=HTMLResponse)
    async def meetings_page(request: Request):
        return templates.TemplateResponse("meetings.html", {"request": request})

    @fastapi_app.get("/calendar", response_class=HTMLResponse)
    async def calendar_page(request: Request):
        return templates.TemplateResponse("calendar.html", {"request": request})

    # API‑роутеры
    fastapi_app.include_router(user_router)
    fastapi_app.include_router(team_router)
    fastapi_app.include_router(task_router)
    fastapi_app.include_router(comment_router)
    fastapi_app.include_router(evaluation_router)
    fastapi_app.include_router(meeting_router)
    fastapi_app.include_router(calendar_router)

    # Admin
    init_admin(fastapi_app)

    return fastapi_app


fastapi_app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:fastapi_app",
        host="127.0.0.1",
        port=8001,
        log_level="info",
        reload=True,
    )
