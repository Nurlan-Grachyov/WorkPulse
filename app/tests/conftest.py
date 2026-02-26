from datetime import datetime, timedelta

import pytest
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload

from app.auth import hash_password
from app.database import Base, get_async_session
from app.main import fastapi_app
from app.models.db_comment import Comment
from app.models.db_evaluation import Evaluation
from app.models.db_meeting import Meeting
from app.models.db_task import Task
from app.models.db_team import Team, TeamUser
from app.models.db_user import User
from app.schemas.scheme_user import RoleCompany, RoleTeam

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


@pytest.fixture
async def db_session(test_db):
    async with TestingSessionLocal() as session:
        await session.rollback()
        yield session
        await session.rollback()


@pytest.fixture
async def app(db_session):
    async def override_get_async_db():
        yield db_session

    fastapi_app.dependency_overrides[get_async_session] = override_get_async_db
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def usual_user(db_session):
    result = await db_session.scalars(
        select(User).where(User.email == "usual_user@example.com")
    )
    usual_user = result.one_or_none()

    if usual_user is None:
        raw_password = "12345"
        hashed_password = hash_password(raw_password)
        usual_user = User(
            email="usual_user@example.com",
            hashed_password=hashed_password,
            role=RoleCompany.USER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(usual_user)
        await db_session.commit()
        await db_session.refresh(usual_user)

    yield usual_user


@pytest.fixture
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

    yield admin


@pytest.fixture
async def team_manager_user(db_session: AsyncSession) -> User:
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

    yield user


@pytest.fixture
async def create_team_with_users(db_session, team_manager_user, usual_user):
    result_team = await db_session.scalars(
        select(Team).where(Team.title == "team with users")
    )
    new_team = result_team.one_or_none()
    if new_team is None:
        new_team = Team(title="team with users", slug="team_with_users")
        db_session.add(new_team)
        await db_session.commit()
        await db_session.refresh(new_team)

    result_existing_links = await db_session.scalars(
        select(TeamUser).where(
            and_(
                TeamUser.team_id == new_team.id,
                TeamUser.user_id.in_([team_manager_user.id, usual_user.id]),
            )
        )
    )
    existing_links = result_existing_links.all()

    existing_user_ids = {link.user_id for link in existing_links}

    new_links = []
    for user_id, role in [
        (team_manager_user.id, RoleTeam.MANAGER),
        (usual_user.id, RoleTeam.USER),
    ]:
        if user_id not in existing_user_ids:
            new_links.append(TeamUser(team_id=new_team.id, user_id=user_id, role=role))

    if new_links:
        db_session.add_all(new_links)
        await db_session.commit()

    yield new_team


@pytest.fixture
async def create_team_without_users(db_session):
    result_team = await db_session.scalars(
        select(Team).where(Team.title == "team without users")
    )
    new_team = result_team.one_or_none()
    if new_team is None:
        new_team = Team(title="team without users", slug="team_without_users")
        db_session.add(new_team)
        await db_session.commit()
        await db_session.refresh(new_team)
    yield new_team


@pytest.fixture
async def create_test_task(db_session, create_team_with_users, team_manager_user):
    result_task = await db_session.scalars(
        select(Task).where(Task.title == "test task")
    )
    new_task = result_task.one_or_none()
    if new_task is None:
        result_team_link = await db_session.scalars(
            select(User)
            .options(joinedload(User.team_link))
            .where(User.id == team_manager_user.id)
        )
        user = result_team_link.one_or_none()
        new_task = Task(
            assignee_id=team_manager_user.id,
            title="test task",
            team_id=user.team_link.team_id,
            deadline=datetime(2026, 2, 20, 18, 0),
        )
        db_session.add(new_task)
        await db_session.commit()
        await db_session.refresh(new_task)
    yield new_task

    if new_task:
        await db_session.delete(new_task)
        await db_session.flush()


@pytest.fixture
async def create_test_meeting(create_team_with_users, team_manager_user, db_session):
    current_date_plus_one = datetime.now() + timedelta(days=1)
    meeting = Meeting(title="first meeting", starts_at=current_date_plus_one)
    meeting.users.append(team_manager_user)

    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)

    yield meeting


@pytest.fixture
async def create_test_evaluation(
    create_team_with_users, create_test_task, team_manager_user, db_session
):
    result_evaluation = await db_session.scalars(
        select(Evaluation).where(Evaluation.task_id == create_test_task.id)
    )
    evaluation = result_evaluation.one_or_none()
    if evaluation is None:
        evaluation = Evaluation(evaluation=4, task_id=create_test_task.id)

        db_session.add(evaluation)
        await db_session.refresh(evaluation)
        await db_session.commit()
    yield evaluation


@pytest.fixture
async def create_test_comment(team_manager_user, create_test_task, db_session):
    comment = Comment(
        text="Well done", user_id=team_manager_user.id, task_id=create_test_task.id
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)

    yield comment
