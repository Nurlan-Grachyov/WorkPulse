import pytest
from sqlalchemy import select

from src.application.routers.router_comment import (
    create_comment,
    delete_comment,
    get_comments_by_task,
    get_comments_by_user,
    update_comment,
)
from src.application.schemas.scheme_comment import CommentCreate, CommentUpdate
from src.infrastructure.db.models.db_comment import Comment


@pytest.mark.asyncio
async def test_create_comment(create_test_task, team_manager_user, db_session):
    data_to_comment = CommentCreate(text="Some comment", task_id=create_test_task.id)
    comment = await create_comment(data_to_comment, team_manager_user, db_session)
    assert comment.text == "Some comment"
    assert comment.user_id == team_manager_user.id


@pytest.mark.asyncio
async def test_get_comments_by_task(create_test_task, team_manager_user, db_session):
    comments = await get_comments_by_task(
        create_test_task.id, team_manager_user, db_session
    )
    for comment in comments:
        assert comment.text == "Some comment"
        assert comment.task_id == create_test_task.id


@pytest.mark.asyncio
async def test_get_comments_by_user(create_test_task, team_manager_user, db_session):
    comments = await get_comments_by_user(
        team_manager_user.email, team_manager_user, db_session
    )
    for comment in comments:
        assert comment.text == "Some comment"
        assert comment.task_id == create_test_task.id


@pytest.mark.asyncio
async def test_update_comment(
    create_test_task, team_manager_user, create_test_comment, db_session
):
    data_to_comment = CommentUpdate(text="Good job")
    comment = await update_comment(
        create_test_comment.id, data_to_comment, team_manager_user, db_session
    )
    assert comment.text == "Good job"


@pytest.mark.asyncio
async def test_delete_comment(create_test_comment, db_session, team_manager_user):
    await delete_comment(create_test_comment.id, team_manager_user, db_session)

    result_deleted_comment = await db_session.scalars(
        select(Comment).where(Comment.id == create_test_comment.id)
    )
    deleted_comment = result_deleted_comment.one_or_none()
    assert deleted_comment is None
