from uuid import UUID

from src.infrastructure.db.models.db_user import User


def _aggregate_user_tasks(user: User, skip_self_id: UUID | None = None) -> dict | None:
    """
    Возвращает словарь вида:
    {
        "tasks": { "Task title": оценка или None, ... },
        "average_evaluations": средний балл или None,
    }

    Если передан skip_self_id и user.id == skip_self_id — возвращает None (для менеджера, чтобы пропустить себя).
    """
    if skip_self_id is not None and user.id == skip_self_id:
        return None

    user_tasks: dict[str, int | None] = {}
    total_evaluations = 0
    score_tasks = 0

    for task in user.tasks:
        score = task.evaluation.evaluation if task.evaluation else None
        user_tasks[task.title] = score

        if score is not None:
            total_evaluations += score
            score_tasks += 1

    avg_score = total_evaluations / score_tasks if score_tasks > 0 else None

    return {
        "tasks": user_tasks,
        "average_evaluations": avg_score,
    }
