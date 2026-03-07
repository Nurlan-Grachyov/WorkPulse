from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.application.schemas.scheme_evaluation import EvaluationCreate
from src.domain.evaluations.repositories import EvaluationRepository
from src.infrastructure.db.models.db_evaluation import Evaluation
from src.infrastructure.db.models.db_task import Task
from src.infrastructure.db.models.db_team import Team, TeamUser
from src.infrastructure.db.models.db_user import User


class SqlAlchemyEvaluationRepository(EvaluationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_tasks_evaluation(self, task_id):
        result = await self._session.scalars(
            select(Task).options(joinedload(Task.evaluation)).where(Task.id == task_id)
        )
        task = result.one_or_none()
        return task

    async def get_all_evaluations(self):
        result = await self._session.execute(
            select(Team).options(
                selectinload(Team.members)  # team -> team_users
                .selectinload(TeamUser.user)  # team_user -> user
                .selectinload(User.tasks)  # user -> tasks
                .selectinload(Task.evaluation)  # task -> evaluation
            )
        )
        teams = result.scalars().unique().all()

        return teams

    async def get_team_evaluations(self, current_user: User):
        team_id = current_user.team_link.team_id
        users_result = await self._session.execute(
            select(User)
            .join(TeamUser, TeamUser.user_id == User.id)
            .options(selectinload(User.tasks).selectinload(Task.evaluation))
            .where(TeamUser.team_id == team_id)
        )

        team_members = users_result.scalars().unique().all()

        return team_members

    async def get_own_evaluations(self, current_user: User):
        result = await self._session.scalars(
            select(User)
            .options(joinedload(User.tasks).joinedload(Task.evaluation))
            .where(User.id == current_user.id)
        )

        db_user = result.unique().one_or_none()

        return db_user

    async def save(self, evaluation: Evaluation) -> None:
        try:
            self._session.add(evaluation)
            await self._session.commit()
            await self._session.refresh(evaluation)
        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError("team_has_dependencies") from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            print(exc)
            raise RuntimeError("database_error") from exc
