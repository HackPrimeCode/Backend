from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy import select

from src.api.deps import DbSession, AdminOrOrganizator
from src.enums import HackathonStatus
from src.models.hackathon import Hackathon
from src.schemas.hackathon import HackathonDetailRead, HackathonPublicRead
from src.schemas.auth import InviteJudgesRequest, InviteJudgesResponse

router = APIRouter(prefix="/hackathons", tags=["hackathons"])


@router.get("", response_model=list[HackathonPublicRead])
def list_hackathons(db: DbSession) -> list[Hackathon]:
    stmt = (
        select(Hackathon)
        .where(Hackathon.status != HackathonStatus.DRAFT)
        .order_by(Hackathon.start_date.desc().nullslast(), Hackathon.id.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/{hackathon_id}", response_model=HackathonDetailRead)
def get_hackathon(hackathon_id: int, db: DbSession) -> Hackathon:
    hackathon = db.get(Hackathon, hackathon_id)
    if hackathon is None or hackathon.status == HackathonStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    return hackathon
