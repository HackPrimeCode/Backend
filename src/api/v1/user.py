from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from src.enums import HackathonStatus
from src.api.deps import DbSession, CurrentUser
from src.schemas.auth import UserRead
from src.schemas.user import UserUpdateRequest, UserProfileRead
from src.schemas.hackathon import HackathonRead
from src.models.hackathon_participant import HackathonParticipant
from src.models.team import Team


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

@router.get("/me/profile", response_model=UserProfileRead)
def get_profile(
    db: DbSession,
    current_user: CurrentUser,
):
    participations = db.execute(
        select(HackathonParticipant)
        .options(joinedload(HackathonParticipant.hackathon))
        .where(HackathonParticipant.user_id == current_user.id)
    ).scalars().all()

    active_hackathon = None
    past_hackathons = []

    for p in participations:
        hackathon = p.hackathon

        participants_count = db.scalar(
            select(func.count()).where(
                HackathonParticipant.hackathon_id == hackathon.id
            )
        )

        teams_count = db.scalar(
            select(func.count()).where(
                Team.hackathon_id == hackathon.id
            )
        )

        hackathon_data = HackathonRead(
            **hackathon.__dict__,
            current_participants=participants_count or 0,
            current_teams=teams_count or 0,
        )

        if hackathon.status == HackathonStatus.IN_PROGRESS:
            active_hackathon = hackathon_data

        elif hackathon.status == HackathonStatus.FINISHED:
            past_hackathons.append(hackathon_data)

    return UserProfileRead(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        tech_stack=current_user.tech_stack,
        global_role=current_user.global_role,
        active_hackathon=active_hackathon,
        past_hackathons=past_hackathons,
    )