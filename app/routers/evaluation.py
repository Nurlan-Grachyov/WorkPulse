from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.auth import current_active_user
from app.database import get_async_session
from app.models.db_evaluation import Evaluation
from app.models.db_task import Task
from app.models.db_team import Team, TeamUser
from app.models.db_user import User
from app.schemas.scheme_evaluation import EvaluationCreate, EvaluationGet
from app.schemas.scheme_user import RoleCompany, RoleTeam

evaluation_router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@evaluation_router.post("/create_evaluation", response_model=EvaluationGet)
async def create_evaluation(
    evaluation: EvaluationCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.scalars(
        select(Task)
        .options(joinedload(Task.evaluation))
        .where(Task.id == evaluation.task_id)
    )
    task = result.one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    elif task.evaluation:
        raise HTTPException(
            status_code=409, detail="Evaluation for this task already exists"
        )

    result = await db.execute(
        select(User)
        .options(joinedload(User.team_link))
        .where(User.id == current_user.id)
    )
    user_with_team = result.scalars().one()

    if (
        user_with_team.team_link is None
        or user_with_team.team_link.role is not RoleTeam.MANAGER
    ):
        raise HTTPException(status_code=403, detail="Manager access only")

    evaluation = Evaluation(**evaluation.model_dump())

    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)

    return EvaluationGet.model_validate(evaluation)


@evaluation_router.get("/get_evaluations")
async def get_evaluations(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if current_user.role is not RoleCompany.ADMIN:

        result = await db.execute(
            select(User)
            .options(joinedload(User.team_link))
            .where(User.id == current_user.id)
        )
        user_with_team = result.scalars().one()

        if user_with_team.team_link.role is RoleTeam.MANAGER:
            team_id = user_with_team.team_link.team_id
            users_result = await db.execute(
                select(User)
                .join(TeamUser, TeamUser.user_id == User.id)
                .options(selectinload(User.tasks).selectinload(Task.evaluation))
                .where(TeamUser.team_id == team_id)
            )

            team_members = users_result.scalars().unique().all()

            users_task_evaluations = {}

            for user in team_members:
                if user.id == current_user.id:
                    continue
                user_tasks = {}
                total_evaluations = 0
                score_tasks = 0

                for task in user.tasks:
                    user_tasks[task.title] = (
                        task.evaluation.evaluation if task.evaluation else None
                    )

                    score = task.evaluation.evaluation if task.evaluation else None
                    if score is not None:
                        total_evaluations += score
                        score_tasks += 1

                avg_score = total_evaluations / score_tasks if score_tasks > 0 else None

                users_task_evaluations[user.email] = {
                    "tasks": user_tasks,
                    "average_evaluations": avg_score,
                }

            return users_task_evaluations

        else:
            result = await db.scalars(
                select(User)
                .options(joinedload(User.tasks).joinedload(Task.evaluation))
                .where(User.id == current_user.id)
            )

            db_user = result.unique().one()

            user_evaluations = {}
            total_evaluations = 0
            score_tasks = 0

            for task in db_user.tasks:
                user_evaluations[task.title] = task.evaluation
                score = task.evaluation.evaluation if task.evaluation else None

                if score is not None:
                    total_evaluations += score
                    score_tasks += 1

            avg_score = total_evaluations / score_tasks if score_tasks > 0 else None
            user_evaluations["average_evaluations"] = avg_score

            return user_evaluations

    elif current_user.role is RoleCompany.ADMIN:
        result = await db.execute(
            select(Team).options(
                selectinload(Team.members)  # team -> team_users
                .selectinload(TeamUser.user)  # team_user -> user
                .selectinload(User.tasks)  # user -> tasks
                .selectinload(Task.evaluation)  # task -> evaluation
            )
        )
        teams = result.scalars().unique().all()

        teams_users_task_evaluations = {}

        for team in teams:
            team_users_dict = {}

            for link in team.members:  # TeamUser
                user = link.user
                user_tasks_dict = {}
                total_evaluations = 0
                score_tasks = 0

                for task in user.tasks:
                    user_tasks_dict[task.title] = (
                        task.evaluation.evaluation if task.evaluation else None
                    )
                    score = task.evaluation.evaluation if task.evaluation else None

                    if score is not None:
                        total_evaluations += score
                        score_tasks += 1

                avg_score = total_evaluations / score_tasks if score_tasks > 0 else None
                user_tasks_dict["average_evaluations"] = avg_score

                team_users_dict[user.email] = user_tasks_dict

            teams_users_task_evaluations[team.slug] = team_users_dict

        return teams_users_task_evaluations
