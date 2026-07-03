from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.deps import CurrentUser, DbSession
from src.models.hackathon_participant import HackathonParticipant
from src.schemas.task import HackathonTaskRead, HackathonTasksRead, TaskCreate, TaskUpdate
from src.services.task_service import TaskService, TaskServiceError

router = APIRouter(tags=["tasks"])


def _get_task_service(db: DbSession) -> TaskService:
    return TaskService(db)


def _require_team_member(db: DbSession, team_id: int, user_id: int) -> HackathonParticipant:
    participant = db.scalar(
        select(HackathonParticipant).where(
            HackathonParticipant.team_id == team_id,
            HackathonParticipant.user_id == user_id,
        )
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team membership required",
        )
    return participant


def _handle_service_error(exc: TaskServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/teams/{team_id}/tasks", response_model=HackathonTasksRead)
def get_team_tasks(
    team_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> HackathonTasksRead:
    _require_team_member(db, team_id, current_user.id)
    service = _get_task_service(db)
    try:
        return service.get_board(team_id)
    except TaskServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post(
    "/teams/{team_id}/tasks",
    response_model=HackathonTaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_team_task(
    team_id: int,
    payload: TaskCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> HackathonTaskRead:
    _require_team_member(db, team_id, current_user.id)
    service = _get_task_service(db)
    try:
        return service.create_task(team_id, payload)
    except TaskServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.patch("/teams/{team_id}/tasks/{task_id}", response_model=HackathonTaskRead)
def update_team_task(
    team_id: int,
    task_id: int,
    payload: TaskUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> HackathonTaskRead:
    _require_team_member(db, team_id, current_user.id)
    service = _get_task_service(db)
    try:
        return service.update_task(team_id, task_id, payload)
    except TaskServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.delete("/teams/{team_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_task(
    team_id: int,
    task_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    _require_team_member(db, team_id, current_user.id)
    service = _get_task_service(db)
    try:
        service.delete_task(team_id, task_id)
    except TaskServiceError as exc:
        raise _handle_service_error(exc) from exc
