from fastapi import APIRouter, Depends

from src.api.deps import DbSession, CurrentUser
from src.schemas.auth import UserRead
from src.schemas.user import UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me", response_model=UserRead)
def update_me(
    payload: UserUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        current_user.name = update_data["name"]

    if "tech_stack" in update_data:
        current_user.tech_stack = update_data["tech_stack"]

    db.commit()
    db.refresh(current_user)

    return current_user

@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser):
    return current_user