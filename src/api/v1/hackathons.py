from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func

from src.api.deps import DbSession
from src.enums import HackathonStatus
from src.models.hackathon import Hackathon
from src.models.team import Team
from src.models.hackathon_participant import HackathonParticipant
from src.schemas.hackathon import HackathonRead, HackathonPublicRead
from src.schemas.auth import InviteJudgesRequest, InviteJudgesResponse

router = APIRouter(prefix="/hackathons", tags=["hackathons"])


@router.get("", response_model=list[HackathonPublicRead])
def list_hackathons(db: DbSession):

    participants_subq = (
        select(
            HackathonParticipant.hackathon_id,
            func.count().label("participants_count"),
        )
        .group_by(HackathonParticipant.hackathon_id)
        .subquery()
    )

    teams_subq = (
        select(
            Team.hackathon_id,
            func.count().label("teams_count"),
        )
        .group_by(Team.hackathon_id)
        .subquery()
    )

    stmt = (
        select(
            Hackathon,
            func.coalesce(participants_subq.c.participants_count, 0),
            func.coalesce(teams_subq.c.teams_count, 0),
        )
        .outerjoin(
            participants_subq,
            Hackathon.id == participants_subq.c.hackathon_id,
        )
        .outerjoin(
            teams_subq,
            Hackathon.id == teams_subq.c.hackathon_id,
        )
        .where(Hackathon.status != HackathonStatus.DRAFT)
    )

    results = db.execute(stmt).all()

    return [
        HackathonPublicRead(
            **h.__dict__,
            current_participants=p_count,
            current_teams=t_count,
        )
        for h, p_count, t_count in results
    ]


@router.get("/{hackathon_id}", response_model=HackathonRead)
def get_hackathon(hackathon_id: int, db: DbSession):

    hackathon = db.get(Hackathon, hackathon_id)

    if hackathon is None or hackathon.status == HackathonStatus.DRAFT:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    participants_count = db.scalar(
        select(func.count()).where(
            HackathonParticipant.hackathon_id == hackathon_id
        )
    )

    teams_count = db.scalar(
        select(func.count()).where(
            Team.hackathon_id == hackathon_id
        )
    )

    return HackathonRead(
        **hackathon.__dict__,
        current_participants=participants_count or 0,
        current_teams=teams_count or 0,
    )
