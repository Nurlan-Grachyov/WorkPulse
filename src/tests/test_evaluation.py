import pytest

from src.application.schemas.scheme_evaluation import EvaluationCreate
from src.application.services.service_evaluations import EvaluationService
from src.infrastructure.evaluations.repositories import SqlAlchemyEvaluationRepository
from src.infrastructure.users.repositories import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_create_evaluation(
    create_test_task, create_team_with_users, team_manager_user, db_session
):
    user_repo = SqlAlchemyUserRepository(db_session)
    evaluation_repo = SqlAlchemyEvaluationRepository(db_session)
    evaluation_service = EvaluationService(evaluation_repo, user_repo)

    evaluation_data = EvaluationCreate(evaluation=4, task_id=create_test_task.id)
    created_evaluation = await evaluation_service.create_evaluation(
        team_manager_user, evaluation_data
    )
    assert created_evaluation.evaluation == 4
    assert created_evaluation.task_id == create_test_task.id


@pytest.mark.asyncio
async def test_get_evaluations(
    create_test_evaluation,
    create_test_task,
    create_team_with_users,
    admin_user,
    team_manager_user,
    usual_user,
    db_session,
):
    user_repo = SqlAlchemyUserRepository(db_session)
    evaluation_repo = SqlAlchemyEvaluationRepository(db_session)
    evaluation_service = EvaluationService(evaluation_repo, user_repo)

    evaluations = await evaluation_service.get_evaluations(admin_user)
    assert (
        evaluations.get(create_team_with_users.slug)
        .get(team_manager_user.email)
        .get(create_test_task.title)
        == create_test_evaluation.evaluation
    )

    evaluations = await evaluation_service.get_evaluations(team_manager_user)
    assert evaluations.get(usual_user.email).get("average_evaluations") is None

    evaluations = await evaluation_service.get_evaluations(usual_user)
    assert evaluations.get("average_evaluations") is None
