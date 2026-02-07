from pydantic import BaseModel, field_validator


class EvaluationScheme(BaseModel):
    evaluation: int
    task_id: int

    @field_validator("evaluation")
    @classmethod
    def check_evaluation(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Оценка должна быть от 1 до 5")
        return v
