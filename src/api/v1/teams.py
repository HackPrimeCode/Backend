import uuid

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select

from src.api.deps import CurrentUser, DbSession
from src.enums import HackathonStatus, InviteTargetRole, ParticipantRole
from src.models.hackathon import Hackathon
from src.models.hackathon_participant import HackathonParticipant
from src.models.invite_token import InviteToken
from src.models.team import Team
from src.schemas.team import InviteTokenRead, TeamCreate, TeamCreateResponse
from src.services.email_service import send_invite_email

router = APIRouter(tags=["teams"])


@router.post(
    "/hackathons/{hackathon_id}/teams",
    response_model=TeamCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    hackathon_id: int,
    payload: TeamCreate,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> TeamCreateResponse:
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None or hackathon.status == HackathonStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.status != HackathonStatus.REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teams can only be created during registration",
        )

    existing_participation = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.hackathon_id == hackathon_id,
        )
    )
    if existing_participation is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered for this hackathon",
        )

    team = Team(hackathon_id=hackathon_id, name=payload.team_name)
    db.add(team)
    db.flush()

    participant = HackathonParticipant(
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        team_id=team.id,
        role=ParticipantRole.CAPTAIN,
    )
    db.add(participant)

    invite_tokens: list[InviteTokenRead] = []
    for email in payload.invite_emails:
        if email.lower() == current_user.email.lower():
            continue

        token = InviteToken(
            token=uuid.uuid4(),
            email=email.lower(),
            hackathon_id=hackathon_id,
            target_team_id=team.id,
            target_role=InviteTargetRole.PARTICIPANT,
            is_used=False,
        )
        db.add(token)
        invite_tokens.append(InviteTokenRead(token=str(token.token), email=email.lower()))

    db.commit()
    
    for invite in invite_tokens:
        background_tasks.add_task(
            send_invite_email,
            invite.email,
            invite.token,
            hackathon.title,
            "участник",
    )

    return TeamCreateResponse(
        team_id=team.id,
        team_name=team.name,
        invite_tokens=invite_tokens,
    )
