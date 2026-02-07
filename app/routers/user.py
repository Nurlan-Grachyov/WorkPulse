from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_users import models
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.db_user import User
from app.schemas.scheme_user import Role, UserRead
from auth import (UserManager, current_active_user, current_superuser,
                  get_user_manager)

user_router = APIRouter()


# не удаляет пользователя по имейлу, как вывести принты в консоль, как юзать дебагер в роутерах
@user_router.patch("/users/update", response_model=UserRead, status_code=200)
async def update_user(
    email: str = Query(...),
    role: Role = Query(...),
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
):
    user = await user_manager.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    user.role = role

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": f"Роль пользователя {email} обновлена на {role}"}


@user_router.delete("/delete_me", status_code=204)
async def delete_current_user(
    user: models.UP = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    await user_manager.delete(user)

    return None


# не удаляет пользователя по имейлу, как вывести принты в консоль, как юзать дебагер в роутерах
@user_router.delete("/users/delete", status_code=204)
async def delete_user(
    email: str = Query(...),
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
):
    user = await user_manager.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    await db.delete(user)
    await db.commit()
    return {"message": "Пользователь удален"}
