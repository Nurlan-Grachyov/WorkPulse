from .entities import Task


def update_task_fields(task: Task, fields: dict) -> Task:
    for field, value in fields.items():
        if value is None:
            continue
        if hasattr(task, field):
            setattr(task, field, value)
    return task