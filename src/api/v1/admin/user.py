from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import AdminOrOrganizator, DbSession
from src.schemas.user import AdminUserRead, UserRoleUpdateRequest
from src.models.user import User

router = APIRouter(prefix="/admin/users", tags=["admin-users"])

@router.get(
    "",
    response_model=list[AdminUserRead],
)
def list_users(
    db: DbSession,
    _: AdminOrOrganizator,
):
    stmt = select(User).order_by(User.id.desc())
    return db.scalars(stmt).all()

@router.patch(
    "/{user_id}/role",
    response_model=AdminUserRead,
)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    db: DbSession,
    _: AdminOrOrganizator,
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    user.global_role = payload.global_role

    db.commit()
    db.refresh(user)

    return user

