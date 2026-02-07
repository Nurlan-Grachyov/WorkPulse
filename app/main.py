from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.orm import configure_mappers

import app.models.db_comment  # Comment
import app.models.db_evaluation  # Evaluation
import app.models.db_meeting  # Meeting
import app.models.db_task  # Task
import app.models.db_team  # Team
# import app.models.db_user  # User
from app.models.db_user import User
from app.routers.team import team_router
from app.routers.user import user_router
from app.schemas.scheme_user import UserCreate, UserRead, UserUpdate
from auth import auth_backend, current_active_user, fastapi_users


@asynccontextmanager
async def lifespan(lifespan_app: FastAPI):
    configure_mappers()
    yield


fastapi_app = FastAPI(title="WorkPulse", lifespan=lifespan)

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
    tags=["users"],
)

fastapi_app.include_router(user_router)
fastapi_app.include_router(team_router)


@fastapi_app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:fastapi_app",
        host="127.0.0.1",
        port=8001,
        log_level="info",
        reload=True,
    )
