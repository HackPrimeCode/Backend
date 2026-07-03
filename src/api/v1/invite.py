import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.deps import DbSession, CurrentUser
from src.enums import InviteTargetRole, GlobalRole, ParticipantRole
from src.models.invite_token import InviteToken
from src.models.hackathon_participant import HackathonParticipant

router = APIRouter(prefix="/invite", tags=["invite"])

@router.post("/invites/{token}/accept")
def accept_invite(
    token: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    invite = db.scalar(
        select(InviteToken).where(InviteToken.token == token)
    )

    if invite is None or invite.is_used:
        raise HTTPException(400, "Invalid or already used invite")

    if invite.email != current_user.email:
        raise HTTPException(403, "Invite does not belong to this user")

    if invite.target_role == InviteTargetRole.JUDGE:
        if current_user.global_role == GlobalRole.USER:
            current_user.global_role = GlobalRole.JUDGE

        existing = db.scalar(
            select(HackathonParticipant).where(
                HackathonParticipant.user_id == current_user.id,
                HackathonParticipant.hackathon_id == invite.hackathon_id,
            )
        )

        if not existing:
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