import pytest
from sqlalchemy import select

from src.application.schemas.scheme_comment import CommentCreate, CommentUpdate
from src.application.services.service_comments import CommentService
from src.infrastructure.comments.repositories import SqlAlchemyCommentRepository
from src.infrastructure.db.models.db_comment import Comment
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository


@pytest.mark.asyncio
async def test_create_comment(create_test_task, team_manager_user, db_session):
    task_repo = SqlAlchemyTaskRepository(db_session)
    comment_repo = SqlAlchemyCommentRepository(db_session)
    comment_service = CommentService(comment_repo, task_repo)

    data_to_comment = CommentCreate(text="Some comment", task_id=create_test_task.id)
    comment = await comment_service.create_comment(data_to_comment, team_manager_user)
    assert comment.text == "Some comment"
    assert comment.user_id == team_manager_user.id


@pytest.mark.asyncio
async def test_get_comments_by_task(create_test_task, team_manager_user, db_session):
    task_repo = SqlAlchemyTaskRepository(db_session)
    comment_repo = SqlAlchemyCommentRepository(db_session)
    comment_service = CommentService(comment_repo, task_repo)

    comments = await comment_service.get_comments_by_task(create_test_task.id)
    for comment in comments:
        assert comment.text == "Some comment"
        assert comment.task_id == create_test_task.id


@pytest.mark.asyncio
async def test_get_comments_by_user(create_test_task, team_manager_user, db_session):
    task_repo = SqlAlchemyTaskRepository(db_session)
    comment_repo = SqlAlchemyCommentRepository(db_session)
    comment_service = CommentService(comment_repo, task_repo)

    comments = await comment_service.get_comments_by_user(team_manager_user.email)
    for comment in comments:
        assert comment.text == "Some comment"
        assert comment.task_id == create_test_task.id


@pytest.mark.asyncio
async def test_update_comment(
    create_test_task, team_manager_user, create_test_comment, db_session
):
    task_repo = SqlAlchemyTaskRepository(db_session)
    comment_repo = SqlAlchemyCommentRepository(db_session)
    comment_service = CommentService(comment_repo, task_repo)

    data_to_comment = CommentUpdate(text="Good job")
    comment = await comment_service.update_comment(
        create_test_comment.id, data_to_comment, team_manager_user
    )
    assert comment.text == "Good job"


@pytest.mark.asyncio
async def test_delete_comment(create_test_comment, db_session, team_manager_user):
    task_repo = SqlAlchemyTaskRepository(db_session)
    comment_repo = SqlAlchemyCommentRepository(db_session)
    comment_service = CommentService(comment_repo, task_repo)

    await comment_service.delete_comment(create_test_comment.id, team_manager_user)

    result_deleted_comment = await db_session.scalars(
        select(Comment).where(Comment.id == create_test_comment.id)
    )
    deleted_comment = result_deleted_comment.one_or_none()
    assert deleted_comment is None
