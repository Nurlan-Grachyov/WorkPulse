from dataclasses import dataclass
from uuid import UUID

from src.application.schemas.scheme_user import RoleCompany


@dataclass
class User:
    id: UUID | None
    email: str
    slug: str
    hashed_password: str
    is_active: bool
    role: RoleCompany
    is_verified: bool
