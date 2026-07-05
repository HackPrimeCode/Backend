from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func

from src.api.deps import DbSession
from src.enums import HackathonStatus
from src.models.hackathon import Hackathon
from src.models.team import Team
from src.models.hackathon_participant import HackathonParticipant
from src.models.hackathon_specification import HackathonSpecification
from src.schemas.hackathon import HackathonRead, HackathonPublicRead, HackathonSpecificationRead, HackathonPublicReadWithTask, HackathonSpecificationCreate

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

@router.get(
    "/hackathons/{hackathon_id}/specification",
    response_model=HackathonSpecificationRead,
)
def get_specification(
    hackathon_id: int,
    db: DbSession,
):
    spec = db.scalar(
        select(HackathonSpecification).where(
            HackathonSpecification.hackathon_id == hackathon_id
        )
    )

    if spec is None:
        raise HTTPException(404, "Specification not found")

    return spec

@router.get(
    "/hackathons/{hackathon_id}/details-with-task",
    response_model=HackathonPublicReadWithTask,
)
def get_hackathon_with_task(
    hackathon_id: int,
    db: DbSession,
):
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(404, "Hackathon not found")

    spec = db.scalar(
        select(HackathonSpecification).where(
            HackathonSpecification.hackathon_id == hackathon_id
        )
    )

    participants_count = db.scalar(
        select(func.count()).where(
            HackathonParticipant.hackathon_id == hackathon_id
        )
    ) or 0

    teams_count = db.scalar(
        select(func.count()).where(
            Team.hackathon_id == hackathon_id
        )
    ) or 0

    return HackathonPublicReadWithTask(
        id=hackathon.id,
        title=hackathon.title,
        description=hackathon.description,
        status=hackathon.status,
        place=hackathon.place,
        prizes=hackathon.prizes,
        topics=hackathon.topics,
        min_team_size=hackathon.min_team_size,
        max_team_size=hackathon.max_team_size,
        max_participants=hackathon.max_participants,
        total_participants=participants_count,
        total_teams=teams_count,
        start_date=hackathon.start_date,
        end_date=hackathon.end_date,

        task=spec.task if spec else None,
        task_description=spec.task_description if spec else None,
        functional_requirements=spec.functional_requirements if spec else None,
        technical_limitations=spec.technical_limitations if spec else None,
        evaluation_criteria=spec.evaluation_criteria if spec else None,
        submission_requirements=spec.submission_requirements if spec else None,
        files=spec.files if spec else None,
    )