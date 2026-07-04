import uuid

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from src.api.deps import CurrentUser, DbSession
from src.enums import HackathonStatus, InviteTargetRole, ParticipantRole, GlobalRole
from src.models.hackathon import Hackathon
from src.models.hackathon_participant import HackathonParticipant
from src.models.invite_token import InviteToken
from src.models.team import Team
from src.schemas.team import InviteTokenRead, TeamInviteRequest, TeamCreate, TeamCreateResponse, TeamDetailRead, TeamMemberRead, TeamUpdateRequest
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
) -> TeamCreateResponse:

    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None or hackathon.status != HackathonStatus.REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team creation is not allowed",
        )

    existing = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.hackathon_id == hackathon_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User already participates in this hackathon",
        )

    team = Team(
        hackathon_id=hackathon_id,
        name=payload.team_name,
    )
    db.add(team)
    db.flush()

    participant = HackathonParticipant(
        user_id=current_user.id,
        hackathon_id=hackathon_id,
        team_id=team.id,
        role=ParticipantRole.CAPTAIN,
    )
    db.add(participant)

    db.commit()

    return TeamCreateResponse(
        team_id=team.id,
        team_name=team.name,
        invite_tokens=[],
    )

@router.get("/teams/{team_id}", response_model=TeamDetailRead)
def get_team(
    team_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")


    participation = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == current_user.id,
        )
    )

    if not participation and current_user.global_role not in (
        GlobalRole.ADMIN,
        GlobalRole.ORGANIZATOR,
        GlobalRole.JUDGE,
    ):
        raise HTTPException(403, "Access denied")

    hackathon = db.get(Hackathon, team.hackathon_id)

    members = db.execute(
        select(HackathonParticipant)
        .options(joinedload(HackathonParticipant.user))
        .where(HackathonParticipant.team_id == team_id)
    ).scalars().all()

    invites = db.scalars(
        select(InviteToken).where(
            InviteToken.target_team_id == team_id,
            InviteToken.is_used == False,
        )
    ).all()

    hackathon = db.get(Hackathon, team.hackathon_id)

    return TeamDetailRead(
        id=team.id,
        name=team.name,
        hackathon=hackathon,
        members=[
            TeamMemberRead(
                id=m.user.id,
                name=m.user.name,
                role=m.role,
            )
            for m in members
        ],
        members_count=len(members),
        max_team_size=hackathon.max_team_size,
        pending_invites=[
            InviteTokenRead(
                token=str(inv.token),
                email=inv.email,
            )
            for inv in invites
        ]
        
        ,
    )

@router.post(
    "/teams/{team_id}/invite",
    response_model=list[InviteTokenRead],
)
def invite_to_team(
    team_id: int,
    payload: TeamInviteRequest,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")

    hackathon = db.get(Hackathon, team.hackathon_id)
    if hackathon is None:
        raise HTTPException(404, "Hackathon not found")

    captain = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.role == ParticipantRole.CAPTAIN,
        )
    )
    if captain is None:
        raise HTTPException(403, "Only captain can invite participants")

    current_members = db.scalar(
        select(func.count()).where(
            HackathonParticipant.team_id == team_id
        )
    )

    pending_invites = db.scalar(
        select(func.count()).where(
            InviteToken.target_team_id == team_id,
            InviteToken.is_used == False,
        )
    )

    if hackathon.max_team_size is not None:
        future_size = current_members + pending_invites + len(payload.emails)
        if future_size > hackathon.max_team_size:
            raise HTTPException(400, "Team size limit exceeded")

    created_invites = []

    for email in payload.emails:
        email_lower = email.lower()

        if email_lower == current_user.email.lower():
            continue

        existing_invite = db.scalar(
            select(InviteToken).where(
                InviteToken.email == email_lower,
                InviteToken.target_team_id == team.id,
                InviteToken.is_used == False,
            )
        )
        if existing_invite:
            continue

        token = InviteToken(
            email=email_lower,
            hackathon_id=team.hackathon_id,
            target_team_id=team.id,
            target_role=InviteTargetRole.PARTICIPANT,
            is_used=False,
        )

        db.add(token)
        db.flush()

        created_invites.append(
            InviteTokenRead(
                token=str(token.token),
                email=email_lower,
            )
        )

    db.commit()

    for invite in created_invites:
        background_tasks.add_task(
            send_invite_email,
            invite.email,
            invite.token,
            hackathon.title,
            "участник",
        )

    return created_invites

@router.delete("/teams/{team_id}/members/{user_id}")
def remove_member(
    team_id: int,
    user_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")

    captain = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.role == ParticipantRole.CAPTAIN,
        )
    )

    if not captain:
        raise HTTPException(403, "Only captain can remove members")

    if user_id == current_user.id:
        raise HTTPException(400, "Captain cannot remove himself")

    member = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == user_id,
        )
    )

    if not member:
        raise HTTPException(404, "Member not found")

    db.delete(member)
    db.commit()

    return {"status": "member removed"}

@router.put("/teams/{team_id}", response_model=TeamDetailRead)
def update_team(
    team_id: int,
    payload: TeamUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")

    hackathon = db.get(Hackathon, team.hackathon_id)

    if hackathon.status == HackathonStatus.FINISHED:
        raise HTTPException(400, "Cannot edit team after hackathon finished")

    captain = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.role == ParticipantRole.CAPTAIN,
        )
    )

    if not captain:
        raise HTTPException(403, "Only captain can edit the team")

    team.name = payload.name

    db.commit()
    db.refresh(team)

    return get_team(team_id, db, current_user)

@router.delete("/teams/{team_id}/invites/{token}")
def cancel_invite(
    team_id: int,
    token: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(404, "Team not found")

    captain = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.role == ParticipantRole.CAPTAIN,
        )
    )

    if not captain:
        raise HTTPException(403, "Only captain can cancel invites")

    invite = db.scalar(
        select(InviteToken).where(
            InviteToken.token == token,
            InviteToken.target_team_id == team_id,
            InviteToken.is_used == False,
        )
    )

    if invite is None:
        raise HTTPException(404, "Active invite not found")

    db.delete(invite)
    db.commit()

    return {"status": "invite cancelled"}