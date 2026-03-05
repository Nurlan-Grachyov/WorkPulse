from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_superuser
from src.application.routers.router_user import get_user_service
from src.application.schemas.scheme_team import TeamCreate, TeamGet
from src.application.schemas.scheme_user import RoleTeam, UserReadWithTeamRole
from src.application.services.service_teams import TeamService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_team import TeamUser
from src.infrastructure.db.models.db_user import User
from src.infrastructure.teams.repositories import SqlAlchemyTeamRepository

team_router = APIRouter(tags=["teams"], prefix="/team")


def get_team_service(db: AsyncSession = Depends(get_async_session)) -> TeamService:
    team_repo = SqlAlchemyTeamRepository(db)
    team_service = TeamService(team_repo)

    return team_service


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
        service=Depends(get_team_service),
) -> TeamGet:
    """
    Creates a new team in the system.

    **Validations:**
    - Team title must be unique
    - Superadmin access only

    **Returns:**
    - Created team with generated slug
    """
    try:
        team = await service.create_team(team_in)
        return TeamGet.model_validate(team)
    except PermissionError:
        raise HTTPException(403, detail="You dont have enough rights")
    except LookupError:
        raise HTTPException(404, detail="Assignee is not found")
    except ValueError:
        raise HTTPException(409, detail="Team already exists")
    except SQLAlchemyError:
        raise HTTPException(500, detail="Try later")


@team_router.get(
    "/{slug_team}/users/",
    status_code=200,
    summary="Get all team users",
    description="Returns team users list with preloaded tasks and comments.",
)
async def get_users_of_team(
        slug_team: str,
        superuser: User = Depends(current_superuser),
        service=Depends(get_team_service),
) -> List[UserReadWithTeamRole]:
    """
    Retrieves all users of specific team.

    **Features:**
    - Eager loading of user tasks and comments (selectinload)
    - JOIN through TeamUser association table
    - Superadmin access only
    """
    try:
        users = await service.get_users_of_team(slug_team)
        return [UserReadWithTeamRole.model_validate(user) for user in users]
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )


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
        user_service=Depends(get_user_service),
        team_service=Depends(get_team_service),
) -> TeamUser:
    """
    Adds user to team by creating TeamUser association record.

    **Validations:**
    1. User exists
    2. Team exists
    3. User not already in team (user_id uniqueness per team)

    **Returns:**
    - Confirmation with association details
    """
    try:
        user = await user_service.get_user(slug=slug_team)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"User {user_email} not found")
    try:
        new_team_user = await team_service.add_user_to_team(slug_team, user.id, role)
        return new_team_user
    except ValueError:
        raise HTTPException(409, detail="The user already exists in the team")
    except LookupError:
        raise HTTPException(status_code=404, detail=f"Team {slug_team} not found")


@team_router.patch(
    "/{slug_team}/users/{slug_user}/role/",
    status_code=200,
    summary="Change user role in team",
    description="Changes user role with 'single manager per team' business logic.",
)
async def change_role_user(
        slug_team: str,
        slug_user: str,
        role_data: RoleTeam,
        user_service=Depends(get_user_service),
        team_service=Depends(get_team_service),
        superuser: User = Depends(current_superuser),
) -> TeamUser:
    """
    Changes user role in team enforcing "one manager per team" business rule.

    **Algorithm when promoting to MANAGER:**
    1. Downgrade all current team managers (except new one)
    2. Assign new role to target user

    **Other roles:** Simple role change without side effects.

    **Returns:**
    - Role change confirmation
    """
    # Проверки пользователя
    try:
        user = await user_service.get_user(slug=slug_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="user_not_found")

    # Основная логика с обработкой всех ошибок
    try:
        new_role = await team_service.change_role_user(
            slug_team=slug_team, user=user, role_data=role_data
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)  # "user_not_found" или "team_not_found"
        )
    except ValueError as exc:
        if "integrity_error" in str(exc):
            raise HTTPException(status_code=409, detail="integrity_violation")
        raise HTTPException(status_code=400, detail="bad_request")
    except RuntimeError as exc:
        if "db_error" in str(exc):
            raise HTTPException(status_code=500, detail="database_error")
        raise HTTPException(status_code=500, detail="internal_error")
    except Exception:
        raise HTTPException(status_code=500, detail="unexpected_error")

    return new_role


@team_router.delete(
    "/{slug_team}/",
    status_code=204,
    summary="Delete team",
    description="Superadmin deletes any team (except superadmins).",
)
async def delete_team(
        slug_team: str,
        superuser: User = Depends(current_superuser),
        team_service=Depends(get_team_service),
) -> None:
    try:
        await team_service.delete_team(slug_team)
    except ValueError as exc:
        if "team_not_found" in str(exc) or "not_found" in str(exc):
            raise HTTPException(status_code=404, detail="team_not_found")
        if "dependencies" in str(exc):
            raise HTTPException(status_code=409, detail="team_has_dependencies")
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError:
        raise HTTPException(status_code=500, detail="database_error")
