from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.models.db_team import Team, TeamUser
from app.models.db_user import User
from app.schemas.scheme_team import TeamCreate, TeamGet
from app.schemas.scheme_user import RoleTeam, UserRead, UserReadWithTeamRole
from auth import current_superuser

team_router = APIRouter(tags=["teams"], prefix="/team")


@team_router.post(
    "/create_team",
    response_model=TeamGet,
    status_code=201,
    summary="Create new team",
    description="Creates a team with unique title. Superadmin access only.",
)
async def create_team(
        team_in: TeamCreate,
        superuser: User = Depends(current_superuser),
        db: AsyncSession = Depends(get_async_session),
) -> TeamGet:
    """
    Creates a new team in the system.

    **Validations:**
    - Team title must be unique
    - Superadmin access only

    **Returns:**
    - Created team with generated slug
    """
    # Check team title uniqueness
    existing_team = await db.scalar(
        select(Team).where(Team.title == team_in.title_team)
    )
    if existing_team:
        raise HTTPException(
            status_code=409, detail="Team with this title already exists"
        )

    # Create team (slug generated automatically)
    new_team = Team(title=team_in.title_team)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)  # Refresh to get ID and slug

    return TeamGet.model_validate(new_team)


@team_router.get(
    "/{slug_team}/users/",
    status_code=200,
    summary="Get all team users",
    description="Returns team users list with preloaded tasks and comments.",
)
async def get_users_of_team(
        slug_team: str,
        superuser: User = Depends(current_superuser),
        db: AsyncSession = Depends(get_async_session),
) -> List[UserReadWithTeamRole]:
    """
    Retrieves all users of specific team.

    **Features:**
    - Eager loading of user tasks and comments (selectinload)
    - JOIN through TeamUser association table
    - Superadmin access only
    """
    stmt = select(User) \
        .options(selectinload(User.team_link)) \
        .join(User.team_link) \
        .join(TeamUser.team) \
        .where(Team.slug == slug_team)

    users = (await db.scalars(stmt)).all()

    return [UserReadWithTeamRole.model_validate(user) for user in users] # Return list of all users


@team_router.post(
    "/{slug_team}/users/add_user/",
    status_code=201,
    summary="Add user to team",
    description="Adds existing user to team with specified role.",
)
async def add_user_to_team(
        slug_team: str,
        user_email: str,
        role: RoleTeam,
        superuser: User = Depends(current_superuser),
        db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Adds user to team by creating TeamUser association record.

    **Validations:**
    1. User exists
    2. Team exists
    3. User not already in team (user_id uniqueness per team)

    **Returns:**
    - Confirmation with association details
    """
    # 1. Find user by email
    result_user = await db.scalars(select(User).where(User.email == user_email))
    user = result_user.one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_email} not found")

    # 2. Find team by slug
    result_team = await db.scalars(select(Team).where(Team.slug == slug_team))
    team = result_team.one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {slug_team} not found")

    # 3. Check uniqueness (one user per team)
    result_existing_link = await db.scalars(
        select(TeamUser).where(
            and_(TeamUser.team_id == team.id, TeamUser.user_id == user.id)
        )
    )
    existing_link = result_existing_link.one_or_none()
    if existing_link:
        raise HTTPException(status_code=409, detail="User already in team")

    # 4. Create association record
    new_team_user = TeamUser(
        team_id=team.id, user_id=user.id, role=role  # USER or MANAGER
    )
    db.add(new_team_user)
    await db.commit()

    return {
        "message": "User added to team",
        "team_user": {
            "title_team": team.title,
            "user_email": user.email,
            "role": role.value,  # "user" or "manager"
        },
    }


@team_router.patch(
    "/{slug_team}/users/{slug_user}/role",
    status_code=200,
    summary="Change user role in team",
    description="Changes user role with 'single manager per team' business logic.",
)
async def change_role_user(
        slug_team: str,
        slug_user: str,
        role_data: RoleTeam,
        db: AsyncSession = Depends(get_async_session),
        superuser: User = Depends(current_superuser),
) -> dict:
    """
    Changes user role in team enforcing "one manager per team" business rule.

    **Algorithm when promoting to MANAGER:**
    1. Downgrade all current team managers (except new one)
    2. Assign new role to target user

    **Other roles:** Simple role change without side effects.

    **Returns:**
    - Role change confirmation
    """
    # 1. Validate user existence
    user = await db.scalar(select(User).where(User.slug == slug_user))
    if not user:
        raise HTTPException(status_code=404, detail=f"User {slug_user} not found")

    # 2. Validate team existence
    team = await db.scalar(select(Team).where(Team.slug == slug_team))
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {slug_team} not found")

    # 3. Validate TeamUser association exists
    team_user = await db.scalar(
        select(TeamUser).where(
            and_(TeamUser.team_id == team.id, TeamUser.user_id == user.id)
        )
    )
    if not team_user:
        raise HTTPException(status_code=404, detail="User not in team")

    # 4. 🎯 Business logic: enforce single MANAGER per team
    if role_data == RoleTeam.MANAGER:
        # Bulk downgrade other team managers (atomic operation!)
        await db.execute(
            update(TeamUser)
            .where(
                TeamUser.team_id == team.id,
                TeamUser.role == RoleTeam.MANAGER,
                TeamUser.user_id != user.id,  # Exclude new manager
            )
            .values(role=RoleTeam.USER)
        )

    # 5. Assign new role (USER or MANAGER)
    team_user.role = role_data
    await db.commit()

    return {
        "message": "Role updated successfully!",
        "user_slug": slug_user,
        "team_slug": slug_team,
        "new_role": team_user.role.value,  # "user" or "manager"
    }


@team_router.delete(
    "/{slug_team}/",
    status_code=204,
    summary="Delete team",
    description="Superadmin deletes any team (except superadmins).",
)
async def delete_team(slug_team: str,
                      superuser: User = Depends(current_superuser),
                      db: AsyncSession = Depends(get_async_session)) -> None:
    result = await db.scalars(select(Team).where(Team.slug == slug_team))
    team = result.one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    await db.delete(team)
    await db.commit()
