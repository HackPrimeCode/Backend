import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import DbSession, CurrentUser
from src.enums import InviteTargetRole, GlobalRole, ParticipantRole
from src.models.invite_token import InviteToken
from src.models.hackathon import Hackathon
from src.models.hackathon_participant import HackathonParticipant

router = APIRouter(prefix="/invite", tags=["invite"])


@router.get("/invites/{token}")
def validate_invite(
    token: uuid.UUID,
    db: DbSession,
):
    invite = db.scalar(
        select(InviteToken).where(InviteToken.token == token)
    )

    if invite is None:
        raise HTTPException(404, "Invite not found")

    if invite.is_used:
        raise HTTPException(400, "Invite already used")

    hackathon = db.get(Hackathon, invite.hackathon_id)

    return {
        "email": invite.email,
        "hackathon_id": invite.hackathon_id,
        "hackathon_title": hackathon.title,
        "team_id": invite.target_team_id,
        "team_name": invite.target_team.name if invite.target_team else None,
        "role": invite.target_role,
    }

@router.post("/invites/{token}/accept")
def accept_invite(
    token: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    invite = db.scalar(
        select(InviteToken).where(InviteToken.token == token)
    )

    if invite is None:
        raise HTTPException(400, "Invite not found")

    if invite.is_used:
        raise HTTPException(400, "Invite already used")

    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(403, "Invite does not belong to this user")

    if invite.target_role == InviteTargetRole.PARTICIPANT:

        existing = db.scalar(
            select(HackathonParticipant).where(
                HackathonParticipant.user_id == current_user.id,
                HackathonParticipant.hackathon_id == invite.hackathon_id,
            )
        )

        if existing:
            raise HTTPException(400, "Already participating")

        participant = HackathonParticipant(
            user_id=current_user.id,
            hackathon_id=invite.hackathon_id,
            team_id=invite.target_team_id,
            role=ParticipantRole.PARTICIPANT,
        )

        db.add(participant)

    elif invite.target_role == InviteTargetRole.JUDGE:

        if current_user.global_role != GlobalRole.JUDGE:
            raise HTTPException(403, "User is not judge")

        participant = HackathonParticipant(
            user_id=current_user.id,
            hackathon_id=invite.hackathon_id,
            team_id=None,
            role=ParticipantRole.JUDGE,
        )

        db.add(participant)

    invite.is_used = True
    db.commit()

    return {"status": "accepted"}

@router.post("/invites/{token}/decline")
def decline_invite(
    token: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    invite = db.scalar(
        select(InviteToken).where(InviteToken.token == token)
    )

    if invite is None or invite.is_used:
        raise HTTPException(400, "Invalid invite")

    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(403, "Invite does not belong to this user")

    invite.is_used = True
    db.commit()

    return {"status": "declined"}