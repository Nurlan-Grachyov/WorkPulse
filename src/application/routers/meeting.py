from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.application.auth import current_active_user, has_manager_rights
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_user import User
from src.application.schemas.scheme_meeting import MeetingGet, MeetingCreate
from src.application.schemas.scheme_user import RoleCompany, RoleTeam

meeting_router = APIRouter(prefix="/meetings", tags=["meetings"])


@meeting_router.post(
    "/create_meeting",
    response_model=MeetingGet,
    status_code=status.HTTP_201_CREATED,
    summary="Create new meeting",
    description="Managers or Admins can create meetings. Checks time slot conflicts.",
)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create meeting with role and time conflict validation.

    Raises:
        HTTP 404: User not found
        HTTP 403: Insufficient rights (not Manager or Admin)
        HTTP 409: Time slot already occupied
    """
    # Verify user exists and has required role
    result_user = await db.scalars(
        select(User)
        .options(joinedload(User.team_link))
        .where(User.id == current_user.id)
    )
    db_user = result_user.one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Manager in team OR Company Admin required
    if (
        not (db_user.team_link and db_user.team_link.role == RoleTeam.MANAGER)
        and db_user.role != RoleCompany.ADMIN
    ):
        raise HTTPException(status_code=403, detail="Manager or Admin access only")

    # Check time slot conflict
    result_meeting = await db.scalars(
        select(Meeting).where(Meeting.starts_at == meeting.starts_at)
    )
    if result_meeting.one_or_none():
        raise HTTPException(
            status_code=409, detail="A meeting at this time already exists."
        )

    # Create and persist meeting
    created_meeting = Meeting(**meeting.model_dump())
    created_meeting.users.append(current_user)
    db.add(created_meeting)
    await db.commit()
    await db.refresh(created_meeting, ["users"])

    return MeetingGet.model_validate(created_meeting)


@meeting_router.post("/{meeting_id}/users/add_user/")
async def add_user_to_meeting(
    meeting_id: int,
    user_email: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    # Single query: meeting + participants + their team roles (N+1 prevention)
    result = await db.scalars(
        select(Meeting)
        .options(
            joinedload(Meeting.users).joinedload(
                User.team_link
            )  # Eager load avoids lazy loading
        )
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.unique().one_or_none()

    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Authorization: Admin OR (Manager AND participant)
    is_admin = current_user.role == RoleCompany.ADMIN
    is_manager = await has_manager_rights(current_user.id, db)

    # Check if current_user participates in this meeting
    is_participant = any(user.id == current_user.id for user in db_meeting.users)

    if not (is_admin or (is_manager and is_participant)):
        raise HTTPException(status_code=403, detail="Insufficient rights")

    user_result = await db.scalars(select(User).where(User.email == user_email))
    db_user = user_result.one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if any(user.id == db_user.id for user in db_meeting.users):
        raise HTTPException(status_code=409, detail="User already in meeting")

    # Adding with relationship
    db_meeting.users.append(db_user)
    await db.commit()
    await db.refresh(db_meeting)

    return {
        "message": "User added to meeting",
        "meeting_user": {
            "title_meeting": db_meeting.title,
            "user_email": db_user.email,
        },
    }


@meeting_router.get(
    "/{meeting_id}",
    response_model=MeetingGet,
    summary="Get meeting by title",
    description="Admins see any meeting. Others see only their meetings.",
)
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Retrieve meeting by title with role-based access.

    Args:
        meeting_id: Meeting id (path parameter)

    Raises:
        HTTP 404: Meeting not found or access denied
    """
    result_meeting = await db.scalars(
        select(Meeting)
        .options(joinedload(Meeting.users))
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result_meeting.unique().one_or_none()
    if not db_meeting:
        raise HTTPException(
            status_code=404, detail="Meeting not found or access denied"
        )

    if current_user.role is RoleCompany.ADMIN:
        return MeetingGet.model_validate(db_meeting)
    else:
        is_participant = any(user.id == current_user.id for user in db_meeting.users)
        if not is_participant:
            raise HTTPException(
                status_code=404, detail="Meeting not found or access denied"
            )
    return MeetingGet.model_validate(db_meeting)


@meeting_router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete meeting",
    description="""
    **Admin**: Can delete any meeting.

    **Team Manager**: Can delete only meetings where they are a participant.

    Cascade deletes meeting_participants associations automatically.
    """,
)
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete meeting with strict participant-based authorization for managers.

    Authorization logic:
        * Company Admin: Full access to any meeting
        * Team Manager: Access only to meetings they participate in
        * Others: Forbidden (403)

    Raises:
        HTTP 404: Meeting not found
        HTTP 403: Insufficient rights (non-participant manager or regular user)

    Notes:
        - Single query loads meeting + participants + roles (prevents N+1)
        - Cascade='all, delete-orphan' on Meeting.users auto-cleans associations
    """
    # Single query: meeting + participants + their team roles (N+1 prevention)
    result = await db.scalars(
        select(Meeting)
        .options(
            joinedload(Meeting.users).joinedload(
                User.team_link
            )  # Eager load avoids lazy loading
        )
        .where(Meeting.id == meeting_id)
    )
    db_meeting = result.unique().one_or_none()

    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Authorization: Admin OR (Manager AND participant)
    is_admin = current_user.role == RoleCompany.ADMIN
    is_manager = await has_manager_rights(current_user.id, db)

    # Check if current_user participates in this meeting
    is_participant = any(user.id == current_user.id for user in db_meeting.users)

    if not (is_admin or (is_manager and is_participant)):
        raise HTTPException(status_code=403, detail="Insufficient rights")

    # Cascade deletes meeting_participants rows automatically
    await db.delete(db_meeting)
    await db.commit()

    return None  # 204 No Content
