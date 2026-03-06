from src.application.schemas.scheme_evaluation import EvaluationCreate
from src.domain.evaluations.repositories import EvaluationRepository
from src.domain.evaluations.services import _aggregate_user_tasks
from src.domain.policies.evaluation_permissions import RoleBasedEvaluationAccessPolicy
from src.domain.policies.global_permissions import is_admin, is_manager
from src.domain.users.repositories import UserRepository
from src.infrastructure.db.models.db_user import User


class EvaluationService:
    def __init__(self, evaluation: EvaluationRepository, users: UserRepository):
        self._evaluation = evaluation
        self._users = users

    async def create_evaluation(self, current_user: User, evaluation: EvaluationCreate):
        task = await self.get_tasks_evaluation(evaluation.task_id)
        if task.evaluation:
            raise ValueError("Evaluation for this task already exists")

        user_with_team_link = await self._users.get_user_with_team_link(
            email=current_user.email
        )
        RoleBasedEvaluationAccessPolicy().ensure_can_create(user_with_team_link, task)

        await self._evaluation.save(evaluation)

    async def get_tasks_evaluation(self, task_id):
        task = await self._evaluation.get_tasks_evaluation(task_id)
        if task is None:
            raise LookupError("Task not found")

        return task

    async def get_evaluations(self, current_user: User):
        # Администратор: все команды → команда → юзеры → задачи
        if is_admin(current_user):
            teams = await self._evaluation.get_all_evaluations()

            teams_users_task_evaluations: dict[str, dict[str, dict]] = {}

            for team in teams:
                team_users_dict: dict[str, dict] = {}

                for link in team.members:  # TeamUser
                    user = link.user
                    agg = _aggregate_user_tasks(user)
                    if agg is None:
                        continue

                    # для админа можно вернуть только tasks+avg без вложенного "tasks"
                    team_users_dict[user.email] = {
                        **agg["tasks"],
                        "average_evaluations": agg["average_evaluations"],
                    }

                teams_users_task_evaluations[team.slug] = team_users_dict

            return teams_users_task_evaluations

        # Менеджер: члены его команды (кроме него)
        elif is_manager(current_user):
            team_members = await self._evaluation.get_team_evaluations(current_user)

            users_task_evaluations: dict[str, dict] = {}

            for user in team_members:
                agg = _aggregate_user_tasks(user, skip_self_id=current_user.id)
                if agg is None:
                    continue

                users_task_evaluations[user.email] = agg

            return users_task_evaluations

        # Обычный пользователь: только свои задачи
        else:
            db_user = await self._evaluation.get_own_evaluations(current_user)
            if db_user is None:
                raise LookupError("user_not_found")

            agg = _aggregate_user_tasks(db_user)
            # для обычного пользователя можно вернуть просто dict title -> score + average
            result: dict[str, int | None] = dict(agg["tasks"])
            result["average_evaluations"] = agg["average_evaluations"]

            return result
