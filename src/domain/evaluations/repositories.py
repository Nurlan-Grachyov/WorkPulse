from typing import Protocol

from src.application.schemas.scheme_evaluation import EvaluationCreate
from src.infrastructure.db.models.db_user import User


class EvaluationRepository(Protocol):
    async def get_tasks_evaluation(self, task_id): ...

    async def get_all_evaluations(self): ...

    async def save(self, evaluation: EvaluationCreate): ...

    async def get_team_evaluations(self, current_user: User):
        pass

    async def get_own_evaluations(self, current_user: User):
        pass
