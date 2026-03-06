from src.application.schemas.scheme_user import RoleCompany, RoleTeam


async def is_admin(current_user):
    return current_user.role is RoleCompany.ADMIN


async def is_manager(current_user):
    return current_user.team_link.role is RoleTeam.MANAGER
