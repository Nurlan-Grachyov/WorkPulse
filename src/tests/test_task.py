from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.db_task import Status, Task
from app.routers.task import create_task, delete_task, get_task, update_task
from app.schemas.scheme_task import TaskCreate, TaskUpdate


@pytest.mark.asyncio
async def test_create_task(db_session, create_team_with_users, team_manager_user):
    task = TaskCreate(
        assignee_email="user@example.com",
        title="Fix login bug",
        deadline="2026-02-20T18:00:00",
    )
    task = await create_task(task, team_manager_user, db_session)
    for item in task:
        if item == "title":
            assert task.item == "Fix login bug"
        elif item == "status":
            assert task.item == Status.OPEN
        elif item == "deadline":
            assert task.item == datetime(2026, 2, 20, 18, 0)


@pytest.mark.asyncio
async def test_get_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    task = await get_task(create_test_task.slug, team_manager_user, db_session)
    assert task.title == "test task"


@pytest.mark.asyncio
async def test_update_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    update_to_task = TaskUpdate(title="updated test task")
    updated_task = await update_task(
        create_test_task.slug, update_to_task, team_manager_user, db_session
    )
    assert updated_task.title == "updated test task"


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_delete_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    await delete_task(create_test_task.slug, team_manager_user, db_session)

    result_task = await db_session.scalars(
        select(Task).where(Task.slug == create_test_task.slug)
    )
    assert result_task.one_or_none() is None
