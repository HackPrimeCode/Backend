from fastapi import APIRouter
from sqlalchemy import select, func

from src.enums import HackathonStatus

from src.api.deps import DbSession
from src.models.hackathon import Hackathon
from src.models.judge_score import JudgeScore
from src.models.team import Team
from src.schemas.leaderboard import LeaderboardHackathonItem, TeamLeaderboardRead
router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get(
    "/hackathons",
    response_model=list[LeaderboardHackathonItem],
)
def leaderboard_hackathons(db: DbSession):
    stmt = (
        select(Hackathon.id, Hackathon.title)
        .where(Hackathon.status == HackathonStatus.FINISHED)
        .order_by(Hackathon.end_date.desc())
    )

    results = db.execute(stmt).all()

    return [
        LeaderboardHackathonItem(id=row.id, title=row.title)
        for row in results
    ]


@router.get(
    "/leaderboard/{hackathon_id}",
    response_model=list[TeamLeaderboardRead],
)
def get_leaderboard(
    hackathon_id: int,
    db: DbSession,
):
    scores_subq = (
        select(
            JudgeScore.team_id,
            func.avg(JudgeScore.idea).label("avg_idea"),
            func.avg(JudgeScore.implementation).label("avg_implementation"),
            func.avg(JudgeScore.quality).label("avg_quality"),
            func.avg(JudgeScore.design).label("avg_design"),
        )
        .where(JudgeScore.hackathon_id == hackathon_id)
        .group_by(JudgeScore.team_id)
        .subquery()
    )

    stmt = (
        select(
            Team.id,
            Team.name,
            scores_subq.c.avg_idea,
            scores_subq.c.avg_implementation,
            scores_subq.c.avg_quality,
            scores_subq.c.avg_design,
        )
        .join(scores_subq, Team.id == scores_subq.c.team_id)
        .where(Team.hackathon_id == hackathon_id)
    )

    results = db.execute(stmt).all()

    leaderboard = []

    for row in results:
        avg_idea = row.avg_idea or 0
        avg_implementation = row.avg_implementation or 0
        avg_quality = row.avg_quality or 0
        avg_design = row.avg_design or 0

        average_score = (
            avg_idea + avg_implementation + avg_quality + avg_design
        ) / 4

        leaderboard.append(
            TeamLeaderboardRead(
                team_id=row.id,
                team_name=row.name,
                average_score=round(average_score, 2),
                idea=round(avg_idea, 2),
                implementation=round(avg_implementation, 2),
                quality=round(avg_quality, 2),
                design=round(avg_design, 2),
            )
        )

    leaderboard.sort(key=lambda x: x.average_score, reverse=True)

    return leaderboard
