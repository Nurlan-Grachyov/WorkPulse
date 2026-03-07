from datetime import datetime

import pytest
from sqlalchemy import select

from src.application.schemas.scheme_task import TaskCreate, TaskUpdate
from src.application.services.service_tasks import TaskService
from src.domain.policies.task_permissions import RoleBasedTaskAccessPolicy
from src.infrastructure.db.models.db_task import Task
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository


@pytest.mark.asyncio
async def test_create_task(db_session, create_team_with_users, team_manager_user):
    policy = RoleBasedTaskAccessPolicy()
    task_repo = SqlAlchemyTaskRepository(db_session)
    task_service = TaskService(task_repo, policy)

    task = TaskCreate(
        assignee_email="user@example.com",
        title="Fix login bug",
        deadline="2026-02-20T18:00:00",
    )
    python_task = TaskCreate.model_dump(task)
    task = await task_service.add_task(python_task, team_manager_user)

    assert task.title == "Fix login bug"
    assert task.deadline == datetime(2026, 2, 20, 18, 0)


@pytest.mark.asyncio
async def test_get_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    policy = RoleBasedTaskAccessPolicy()
    task_repo = SqlAlchemyTaskRepository(db_session)
    task_service = TaskService(task_repo, policy)

    task = await task_service.get_task_by_slug_for_team(create_test_task.slug)
    assert task.title == "test task"


@pytest.mark.asyncio
async def test_get_task(
    db_session, create_team_with_users, admin_user, create_test_task
):
    policy = RoleBasedTaskAccessPolicy()
    task_repo = SqlAlchemyTaskRepository(db_session)
    task_service = TaskService(task_repo, policy)

    tasks = await task_service.get_all_task(admin_user)
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_update_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    policy = RoleBasedTaskAccessPolicy()
    task_repo = SqlAlchemyTaskRepository(db_session)
    task_service = TaskService(task_repo, policy)

    update_to_task = TaskUpdate(title="updated test task")
    python_update_to_task = TaskUpdate.model_dump(update_to_task)
    updated_task = await task_service.update_task(
        create_test_task.slug, python_update_to_task, team_manager_user
    )
    assert updated_task.title == "updated test task"


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_delete_task(
    db_session, create_team_with_users, team_manager_user, create_test_task
):
    policy = RoleBasedTaskAccessPolicy()
    task_repo = SqlAlchemyTaskRepository(db_session)
    task_service = TaskService(task_repo, policy)

    await task_service.delete_task(create_test_task.slug, team_manager_user)

    result_task = await db_session.scalars(
        select(Task).where(Task.slug == create_test_task.slug)
    )
    assert result_task.one_or_none() is None
