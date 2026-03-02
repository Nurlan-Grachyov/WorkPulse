import os

from dotenv import load_dotenv
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.application.auth import verify_password
from src.infrastructure.db.database import engine
from src.infrastructure.db.models.db_comment import Comment
from src.infrastructure.db.models.db_evaluation import Evaluation
from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_task import Task
from src.infrastructure.db.models.db_team import Team
from src.infrastructure.db.models.db_user import User
from src.application.schemas.scheme_user import RoleCompany


class MeetingAdmin(ModelView, model=Meeting):
    column_list = [Meeting.id, Meeting.title, Meeting.starts_at]
    column_searchable_list = [Meeting.title]
    page_size = 20


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.title]
    column_searchable_list = [Team.title]
    page_size = 20


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.title, Task.description, Task.status]
    column_searchable_list = [Task.title]
    page_size = 20


class EvaluationAdmin(ModelView, model=Evaluation):
    column_list = [Evaluation.id, Evaluation.task_id, Evaluation.evaluation]
    page_size = 20


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.text, Comment.written_at]
    column_searchable_list = [Comment.text]
    page_size = 20


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role]


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


class AdminAuthBackend(AuthenticationBackend):
    def __init__(self, secret_key: str = SECRET_KEY):
        super().__init__(secret_key=secret_key)
        self.user = None

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        async with AsyncSession(engine) as session:
            result = await session.scalars(select(User).where(User.email == username))
            user = result.one_or_none()

            if user and verify_password(password, user.hashed_password):
                if user.role != RoleCompany.ADMIN:
                    return False

                request.session["user"] = {
                    "email": user.email,
                }
                return True
        return False

    async def logout(self, request: Request) -> bool:
        self.user = None
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_info = request.session.get("user")
        if not user_info:
            return False
        return True


def init_admin(app):
    """Подключаем sqladmin к конкретному экземпляру FastAPI."""
    auth_backend = AdminAuthBackend()
    admin = Admin(app, engine, authentication_backend=auth_backend)
    admin.add_view(MeetingAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(EvaluationAdmin)
    admin.add_view(CommentAdmin)
