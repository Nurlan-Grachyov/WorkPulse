import pytest

from app.routers.evaluation import create_evaluation, get_evaluations
from app.schemas.scheme_evaluation import EvaluationCreate


@pytest.mark.asyncio
async def test_create_evaluation(
    create_test_task, create_team_with_users, team_manager_user, db_session
):
    evaluation_data = EvaluationCreate(evaluation=4, task_id=create_test_task.id)
    created_evaluation = await create_evaluation(
        evaluation_data, team_manager_user, db_session
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
    evaluations = await get_evaluations(admin_user, db_session)
    assert (
        evaluations.get(create_team_with_users.slug)
        .get(team_manager_user.email)
        .get(create_test_task.title)
        == create_test_evaluation.evaluation
    )

    evaluations = await get_evaluations(team_manager_user, db_session)
    assert evaluations.get(usual_user.email).get("average_evaluations") is None

    evaluations = await get_evaluations(usual_user, db_session)
    assert evaluations.get("average_evaluations") is None
