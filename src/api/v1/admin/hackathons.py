import json
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy import select, func

from src.enums import InviteTargetRole, GlobalRole

from src.api.deps import AdminOrOrganizator, DbSession
from src.core.storage import s3_storage
from src.enums import HackathonStatus, HackPlace
from src.services.email_service import send_invite_email
from src.models.hackathon import Hackathon
from src.models.hackathon_participant import HackathonParticipant
from src.models.team import Team
from src.models.hackathon_specification import HackathonSpecification
from src.models.prizes import HackathonPrize
from src.models.invite_token import InviteToken
from src.schemas.hackathon import (
    HackathonRead,
    HackathonAdminListItem,
    HackathonStatusUpdate,
    HackathonSpecificationRead,
    HackathonUpdate,
    HackathonSpecificationCreate,
    AdminTeamStatsRead,
    HackathonAdminDetailedStats,
    AdminHackathonDetailRead
)
from src.schemas.auth import InviteJudgesRequest, InviteJudgesResponse


router = APIRouter(prefix="/admin/hackathons", tags=["admin-hackathons"])


def _parse_json_list(raw: str | None, field_name: str) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be valid JSON array",
        ) from exc
    if not isinstance(value, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be a JSON array",
        )
    return value


def _parse_optional_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid datetime format, use ISO 8601",
        ) from exc


@router.post("", response_model=HackathonRead, status_code=status.HTTP_201_CREATED)
def create_hackathon(
    db: DbSession,
    _: AdminOrOrganizator,
    title: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    topics: Annotated[str | None, Form()] = None,
    prizes: Annotated[str | None, Form()] = None,
    place: Annotated[HackPlace, Form()] = HackPlace.ONLINE,
    min_team_size: Annotated[int, Form()] = None,
    max_team_size: Annotated[int, Form()] = None,
    max_participants: Annotated[int, Form()] = None,
    start_date: Annotated[str | None, Form()] = None,
    end_date: Annotated[str | None, Form()] = None,
    tz_file: Annotated[UploadFile | None, File()] = None,
) -> Hackathon:

    prizes_data = _parse_json_list(prizes, "prizes")

    hackathon = Hackathon(
        title=title,
        description=description,
        topics=_parse_json_list(topics, "topics"),
        min_team_size=min_team_size,
        max_team_size=max_team_size,
        max_participants=max_participants,
        place = place,
        start_date=_parse_optional_datetime(start_date),
        end_date=_parse_optional_datetime(end_date),
        status=HackathonStatus.REGISTRATION,
    )


    for prize in prizes_data:
        hackathon.prizes.append(
            HackathonPrize(
                title=prize["title"],
                reward=prize["reward"],
            )
        )

    db.add(hackathon)
    db.flush()

    if tz_file is not None and tz_file.filename:
        try:
            hackathon.tz_file_url = s3_storage.upload_hackathon_tz(
                hackathon.id, tz_file
            )
        except ValueError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    db.commit()
    db.refresh(hackathon)

    return hackathon


@router.get(
    "/hack_list",
    response_model=list[HackathonAdminListItem],
)
def list_hackathons_for_admin(
    db: DbSession,
    _: AdminOrOrganizator,
):
    stmt = (
        select(Hackathon.id, Hackathon.title)
        .order_by(Hackathon.id.desc())
    )

    results = db.execute(stmt).all()

    return [
        HackathonAdminListItem(id=row.id, title=row.title)
        for row in results
    ]

@router.get(
    "/{hackathon_id}",
    response_model=AdminHackathonDetailRead,
)
def get_admin_hackathon_detail(
    hackathon_id: int,
    db: DbSession,
    _: AdminOrOrganizator,
):
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(404, "Hackathon not found")


    participants_count = db.scalar(
        select(func.count()).where(
            HackathonParticipant.hackathon_id == hackathon_id
        )
    ) or 0

    teams = db.scalars(
        select(Team).where(Team.hackathon_id == hackathon_id)
    ).all()

    team_ids = [team.id for team in teams]

    members_counts = dict(
        db.execute(
            select(
                HackathonParticipant.team_id,
                func.count().label("members_count"),
            )
            .where(HackathonParticipant.team_id.in_(team_ids))
            .group_by(HackathonParticipant.team_id)
        ).all()
    )

    teams_data = [
        AdminTeamStatsRead(
            id=team.id,
            name=team.name,
            members_count=members_counts.get(team.id, 0),
        )
        for team in teams
    ]

    spec = db.scalar(
        select(HackathonSpecification).where(
            HackathonSpecification.hackathon_id == hackathon_id
        )
    )

    submission_requirements = (
    hackathon.specification.submission_requirements
    if hackathon.specification
    else []
    )

    return AdminHackathonDetailRead(
        id=hackathon.id,
        title=hackathon.title,
        description=hackathon.description,
        status=hackathon.status,
        place=hackathon.place,
        min_team_size=hackathon.min_team_size,
        max_team_size=hackathon.max_team_size,
        max_participants=hackathon.max_participants,
        submission_requirements=submission_requirements,
        total_participants=participants_count,
        total_teams=len(teams),
        start_date=hackathon.start_date,
        end_date=hackathon.end_date,
        topics=hackathon.topics,
        prizes=hackathon.prizes,
        specification=spec,
        teams=teams_data,
    )

@router.patch("/{hackathon_id}/status", response_model=HackathonRead)
def update_hackathon_status(
    hackathon_id: int,
    payload: HackathonStatusUpdate,
    db: DbSession,
    _: AdminOrOrganizator,
) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    hackathon.status = payload.status
    db.commit()
    db.refresh(hackathon)
    return hackathon

@router.patch("/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(
    hackathon_id: int,
    payload: HackathonUpdate,
    db: DbSession,
    _: AdminOrOrganizator,
) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hackathon not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    prizes = update_data.pop("prizes", None)

    for field, value in update_data.items():
        setattr(hackathon, field, value)

    if prizes is not None:
        hackathon.prizes.clear()

        for prize_data in prizes:
            hackathon.prizes.append(
                HackathonPrize(
                    title=prize_data["title"],
                    reward=prize_data["reward"],
                )
            )

    db.commit()
    db.refresh(hackathon)
    return hackathon

@router.post(
    "/{hackathon_id}/invite-judges",
    response_model=InviteJudgesResponse,
)
def invite_judges(
    hackathon_id: int,
    payload: InviteJudgesRequest,
    db: DbSession,
    _: AdminOrOrganizator,
    background_tasks: BackgroundTasks,
):
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(
            status_code=404,
            detail="Hackathon not found",
        )

    created_invites = []

    for email in payload.emails:
        email_lower = email.lower()

        existing_invite = db.scalar(
            select(InviteToken).where(
                InviteToken.email == email_lower,
                InviteToken.hackathon_id == hackathon_id,
                InviteToken.target_role == InviteTargetRole.JUDGE,
                InviteToken.is_used == False,
            )
        )

        if existing_invite:
            continue

        token = InviteToken(
            email=email_lower,
            hackathon_id=hackathon_id,
            target_team_id=None,
            target_role=InviteTargetRole.JUDGE,
            is_used=False,
        )

        db.add(token)
        db.flush()

        created_invites.append(token)

    db.commit()

    for invite in created_invites:
        background_tasks.add_task(
            send_invite_email,
            invite.email,
            invite.token,
            hackathon.title,
            "жюри",
        )

    return InviteJudgesResponse(
        created_invites=[str(inv.token) for inv in created_invites]
    )

@router.post(
    "/{hackathon_id}/specification",
    response_model=HackathonSpecificationRead,
)
def create_specification(
    hackathon_id: int,
    payload: HackathonSpecificationCreate,
    db: DbSession,
    _: AdminOrOrganizator,
):
    existing = db.scalar(
        select(HackathonSpecification).where(
            HackathonSpecification.hackathon_id == hackathon_id
        )
    )

    if existing:
        raise HTTPException(400, "Specification already exists")

    spec = HackathonSpecification(
        hackathon_id=hackathon_id,
        **payload.model_dump()
    )

    db.add(spec)
    db.commit()
    db.refresh(spec)

    return spec

@router.put(
    "/{hackathon_id}/specification",
    response_model=HackathonSpecificationRead,
)
def update_specification(
    hackathon_id: int,
    payload: HackathonSpecificationCreate,
    db: DbSession,
    _: AdminOrOrganizator,
):
    spec = db.scalar(
        select(HackathonSpecification).where(
            HackathonSpecification.hackathon_id == hackathon_id
        )
    )

    if spec is None:
        raise HTTPException(404, "Specification not found")

    for field, value in payload.model_dump().items():
        setattr(spec, field, value)

    db.commit()
    db.refresh(spec)

    return spec
