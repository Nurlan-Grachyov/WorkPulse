from .entities import Task


def update_task_fields(task: Task, **fields) -> Task:
    for field, value in fields.items():
        if hasattr(task, field) and value is not None:
            setattr(task, field, value)
    return task