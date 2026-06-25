import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from src.api.deps import AdminOrOrganizator, DbSession
from src.core.storage import s3_storage
from src.enums import HackathonStatus
from src.models.hackathon import Hackathon
from src.models.topics import Topic
from src.models.prizes import HackathonPrize
from src.schemas.hackathon import HackathonRead, HackathonStatusUpdate, HackathonUpdate

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
    technologies: Annotated[str | None, Form()] = None,
    prizes: Annotated[str | None, Form()] = None,
    start_date: Annotated[str | None, Form()] = None,
    end_date: Annotated[str | None, Form()] = None,
    submission_requirements: Annotated[str | None, Form()] = None,
    evaluation_criteria: Annotated[str | None, Form()] = None,
    tz_file: Annotated[UploadFile | None, File()] = None,
) -> Hackathon:

    topics_data = _parse_json_list(topics, "topics")
    prizes_data = _parse_json_list(prizes, "prizes")

    hackathon = Hackathon(
        title=title,
        description=description,
        technologies=_parse_json_list(technologies, "technologies"),
        start_date=_parse_optional_datetime(start_date),
        end_date=_parse_optional_datetime(end_date),
        submission_requirements=_parse_json_list(submission_requirements, "submission_requirements"),
        evaluation_criteria=_parse_json_list(evaluation_criteria, "evaluation_criteria"),
        status=HackathonStatus.DRAFT,
    )


    for topic in topics_data:
        hackathon.topics.append(
            Topic(
                name=topic["name"],
                description=topic.get("description"),
            )
        )


    for prize in prizes_data:
        hackathon.prizes.append(
            HackathonPrize(
                place=prize["place"],
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


@router.put("/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(
    hackathon_id: int,
    payload: HackathonUpdate,
    db: DbSession,
    _: AdminOrOrganizator,
) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    if hackathon.status not in (HackathonStatus.DRAFT, HackathonStatus.REGISTRATION):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hackathon can only be edited before it starts",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hackathon, field, value)

    db.commit()
    db.refresh(hackathon)
    return hackathon


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
