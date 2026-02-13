from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_async_session
from app.models.db_task import Task
from app.models.db_user import User
from app.schemas.scheme_task import TaskCreate, TaskGet, TaskUpdate
from app.schemas.scheme_user import RoleTeam
from auth import current_active_user

task_router = APIRouter(prefix="/tasks", tags=["tasks"])


@task_router.get(
    "/{slug}",
    response_model=TaskGet,
    summary="Get task by slug",
    description="Return a single task by slug. Accessible only for members of the same team.",
    status_code=200,
)
async def get_task(
        slug: str,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session),
) -> TaskGet:
    """
    Get a single task by its slug within the current user's team.

    - Ensures the task belongs to the same team as the current user.
    - Raises 404 if the task does not exist or belongs to another team.
    """

    result = await db.scalars(select(User).options(joinedload(User.team_link)).where(User.id == current_user.id))
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result_task = await db.scalars(
        select(Task).where(
            Task.slug == slug,
            Task.team_id == user.team_link.team_id,
        )
    )
    task = result_task.one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskGet.model_validate(task)


@task_router.post(
    "/create_task",
    response_model=TaskGet,
    summary="Create a new task",
    description="Create a new task. Manager access only.",
    status_code=201,
)
async def create_task(
        task: TaskCreate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session),
) -> TaskGet:
    """
    Create a new task inside the current user's team.

    - Only users with MANAGER role can create tasks.
    - The task is automatically bound to the manager's team and user.
    """
    result = await db.execute(
        select(User)
        .options(joinedload(User.team_link))
        .where(User.id == current_user.id)
    )
    user_with_team = result.scalars().one()

    if user_with_team.team_link.role is not RoleTeam.MANAGER:
        raise HTTPException(status_code=403, detail="Manager access only")

    team_id = current_user.team_link.team_id

    assignee_result = await db.scalars(
        select(User).where(User.email == task.assignee_email, User.is_active)
    )
    assignee = assignee_result.one_or_none()

    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")

    # Bind task to current manager and their team
    db_task = Task(
        **task.model_dump(exclude={'assignee_email'}),
        team_id=team_id,
        assignee_id=assignee.id,
    )

    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return TaskGet.model_validate(db_task)


@task_router.patch(
    "/{slug}",
    response_model=TaskGet,
    summary="Update an existing task",
    description="Partially update a task. Manager access only.",
    status_code=200,
)
async def update_task(
        slug: str,
        task: TaskUpdate,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session),
) -> TaskGet:
    """
    Partially update a task identified by slug within the manager's team.

    - Only managers of the team can update a task.
    - Supports partial update via TaskUpdate (PATCH semantics).
    """
    result = await db.execute(
        select(User)
        .options(joinedload(User.team_link))
        .where(User.id == current_user.id)
    )
    user_with_team = result.scalars().one()

    if user_with_team.team_link.role is not RoleTeam.MANAGER:
        raise HTTPException(status_code=403, detail="Manager access only")

    result_task = await db.scalars(
        select(Task).where(
            Task.slug == slug,
            Task.team_id == current_user.team_link.team_id,
        )
    )
    db_task = result_task.one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Apply only provided fields (exclude_unset keeps PATCH behavior)
    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    await db.commit()
    await db.refresh(db_task)

    return TaskGet.model_validate(db_task)


@task_router.delete(
    "/{slug}",
    response_model=None,
    summary="Delete a task",
    description="Delete a task by slug. Manager access only.",
    status_code=204,
)
async def delete_task(
        slug: str,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete a task by its slug within the manager's team.

    - Only managers can delete tasks.
    - Raises 404 if the task is not found in the manager's team.
    """
    result = await db.execute(
        select(User)
        .options(joinedload(User.team_link))
        .where(User.id == current_user.id)
    )
    user_with_team = result.scalars().one()

    if user_with_team.team_link.role is not RoleTeam.MANAGER:
        raise HTTPException(status_code=403, detail="Manager access only")

    result = await db.scalars(
        select(Task).where(
            Task.slug == slug,
            Task.team_id == current_user.team_link.team_id,
        )
    )
    task = result.one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
