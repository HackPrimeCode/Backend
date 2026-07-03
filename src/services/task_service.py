from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.enums import ParticipantRole, TaskStatus
from src.models.hackathon_participant import HackathonParticipant
from src.models.hackathon_task import HackathonTask
from src.models.team import Team
from src.schemas.task import (
    HackathonTaskRead,
    HackathonTasksRead,
    TaskAssigneeRead,
    TaskColumnsRead,
    TaskCreate,
    TaskUpdate,
    TeamMemberRead,
)

AVATAR_COLORS = (
    "#6366f1",
    "#8b5cf6",
    "#ec4899",
    "#f97316",
    "#14b8a6",
    "#0ea5e9",
    "#84cc16",
    "#ef4444",
)

TASK_COLUMN_KEYS = (
    TaskStatus.BACKLOG,
    TaskStatus.IN_WORK,
    TaskStatus.REVIEW,
    TaskStatus.DONE,
)


class TaskServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_board(self, team_id: int) -> HackathonTasksRead:
        team = self._get_team(team_id)
        members = self._get_team_members(team_id)
        tasks = self._get_team_tasks(team_id)
        return HackathonTasksRead(
            team_id=str(team.id),
            team_members=[self._to_team_member(member) for member in members],
            tasks=self._group_tasks(tasks),
        )

    def create_task(self, team_id: int, payload: TaskCreate) -> HackathonTaskRead:
        self._get_team(team_id)
        if payload.assignee_id is not None:
            self._validate_assignee(team_id, payload.assignee_id)

        position = self._next_position(team_id, TaskStatus.BACKLOG)
        task = HackathonTask(
            team_id=team_id,
            title=payload.title,
            tag=payload.tag,
            description=payload.description,
            status=TaskStatus.BACKLOG,
            position=position,
            assignee_id=payload.assignee_id,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return self._to_task_read(self._get_task_with_assignee(task.id))

    def update_task(self, team_id: int, task_id: int, payload: TaskUpdate) -> HackathonTaskRead:
        task = self._get_task_for_team(team_id, task_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "assignee_id" in update_data and update_data["assignee_id"] is not None:
            self._validate_assignee(team_id, update_data["assignee_id"])

        new_status = update_data.get("status", task.status)
        if new_status != task.status:
            task.status = new_status
            task.position = update_data.get("position", self._next_position(team_id, new_status))
        elif "position" in update_data and update_data["position"] is not None:
            task.position = update_data["position"]

        for field in ("title", "tag", "description", "assignee_id"):
            if field in update_data:
                setattr(task, field, update_data[field])

        self.db.commit()
        self.db.refresh(task)
        return self._to_task_read(self._get_task_with_assignee(task.id))

    def delete_task(self, team_id: int, task_id: int) -> None:
        task = self._get_task_for_team(team_id, task_id)
        self.db.delete(task)
        self.db.commit()

    def _get_team(self, team_id: int) -> Team:
        team = self.db.get(Team, team_id)
        if team is None:
            raise TaskServiceError("Team not found", status_code=404)
        return team

    def _get_team_members(self, team_id: int) -> list[HackathonParticipant]:
        stmt = (
            select(HackathonParticipant)
            .where(HackathonParticipant.team_id == team_id)
            .options(joinedload(HackathonParticipant.user))
            .order_by(HackathonParticipant.id)
        )
        return list(self.db.scalars(stmt).all())

    def _get_team_tasks(self, team_id: int) -> list[HackathonTask]:
        stmt = (
            select(HackathonTask)
            .where(HackathonTask.team_id == team_id)
            .options(
                joinedload(HackathonTask.assignee).joinedload(HackathonParticipant.user),
            )
            .order_by(HackathonTask.status, HackathonTask.position, HackathonTask.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def _get_task_for_team(self, team_id: int, task_id: int) -> HackathonTask:
        task = self.db.scalar(
            select(HackathonTask).where(
                HackathonTask.id == task_id,
                HackathonTask.team_id == team_id,
            )
        )
        if task is None:
            raise TaskServiceError("Task not found", status_code=404)
        return task

    def _get_task_with_assignee(self, task_id: int) -> HackathonTask:
        task = self.db.scalar(
            select(HackathonTask)
            .where(HackathonTask.id == task_id)
            .options(
                joinedload(HackathonTask.assignee).joinedload(HackathonParticipant.user),
            )
        )
        if task is None:
            raise TaskServiceError("Task not found", status_code=404)
        return task

    def _validate_assignee(self, team_id: int, assignee_id: int) -> None:
        assignee = self.db.scalar(
            select(HackathonParticipant).where(
                HackathonParticipant.id == assignee_id,
                HackathonParticipant.team_id == team_id,
            )
        )
        if assignee is None:
            raise TaskServiceError("Assignee must be a member of this team")

    def _next_position(self, team_id: int, status: TaskStatus) -> int:
        max_position = self.db.scalar(
            select(func.max(HackathonTask.position)).where(
                HackathonTask.team_id == team_id,
                HackathonTask.status == status,
            )
        )
        return (max_position or -1) + 1

    def _group_tasks(self, tasks: list[HackathonTask]) -> TaskColumnsRead:
        grouped: dict[TaskStatus, list[HackathonTaskRead]] = {
            status: [] for status in TASK_COLUMN_KEYS
        }
        for task in tasks:
            grouped[task.status].append(self._to_task_read(task))
        return TaskColumnsRead(
            backlog=grouped[TaskStatus.BACKLOG],
            in_work=grouped[TaskStatus.IN_WORK],
            review=grouped[TaskStatus.REVIEW],
            done=grouped[TaskStatus.DONE],
        )

    def _to_team_member(self, participant: HackathonParticipant) -> TeamMemberRead:
        user = participant.user
        return TeamMemberRead(
            id=participant.id,
            user_id=participant.user_id,
            team_id=participant.team_id,
            email=user.email,
            name=user.name or user.email,
            skills=user.tech_stack or [],
            is_captain=participant.role == ParticipantRole.CAPTAIN,
            avatar_color=self._resolve_avatar_color(participant),
        )

    def _to_task_read(self, task: HackathonTask) -> HackathonTaskRead:
        assignee = None
        if task.assignee is not None and task.assignee.user is not None:
            user = task.assignee.user
            assignee = TaskAssigneeRead(
                name=user.name or user.email,
                color=self._resolve_avatar_color(task.assignee),
            )
        return HackathonTaskRead(
            id=str(task.id),
            title=task.title,
            tag=task.tag,
            description=task.description,
            assignee=assignee,
        )

    @staticmethod
    def _resolve_avatar_color(participant: HackathonParticipant) -> str:
        if participant.avatar_color:
            return participant.avatar_color
        return AVATAR_COLORS[participant.id % len(AVATAR_COLORS)]
