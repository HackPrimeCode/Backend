from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.enums import GlobalRole, ParticipantRole

from src.api.deps import DbSession, CurrentUser
from src.schemas.score import JudgeScoreCreate
from src.models.hackathon_participant import HackathonParticipant
from src.models.judge_score import JudgeScore
from src.models.team import Team

router = APIRouter(prefix="/judge", tags=["judge"])

@router.post(
    "/hackathons/{hackathon_id}/teams/{team_id}/score",
)
def submit_score(
    hackathon_id: int,
    team_id: int,
    payload: JudgeScoreCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    if current_user.global_role != GlobalRole.JUDGE:
        raise HTTPException(403, "Only judges can submit scores")

    judge_participation = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.user_id == current_user.id,
            HackathonParticipant.hackathon_id == hackathon_id,
            HackathonParticipant.role == ParticipantRole.JUDGE,
        )
    )

    if not judge_participation:
        raise HTTPException(403, "Judge is not assigned to this hackathon")

    team = db.scalar(
        select(Team).where(
            Team.id == team_id,
            Team.hackathon_id == hackathon_id,
        )
    )

    if not team:
        raise HTTPException(404, "Team not found")

    existing_score = db.scalar(
        select(JudgeScore).where(
            JudgeScore.team_id == team_id,
            JudgeScore.judge_id == current_user.id,
        )
    )

    if existing_score:
        existing_score.idea = payload.idea
        existing_score.implementation = payload.implementation
        existing_score.quality = payload.quality
        existing_score.design = payload.design

        db.commit()
        return {"status": "score updated"}

    score = JudgeScore(
        hackathon_id=hackathon_id,
        team_id=team_id,
        judge_id=current_user.id,
        idea=payload.idea,
        implementation=payload.implementation,
        quality=payload.quality,
        design=payload.design,
    )

    db.add(score)
    db.commit()

    return {"status": "score submitted"}