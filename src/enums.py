import enum


class GlobalRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    ORGANIZATOR = "organizator"

class HackPlace(str, enum.Enum):
    MOSCOW = "Москва"
    SPB = "Санкт-Петербург"
    KAZAN = "Казань"
    NOVGOROD = "Нижний-Новгород"
    ONLINE = "Онлайн"


class HackathonStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REGISTRATION = "REGISTRATION"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class ParticipantRole(str, enum.Enum):
    CAPTAIN = "captain"
    PARTICIPANT = "participant"
    JUDGE = "judge"


class InviteTargetRole(str, enum.Enum):
    PARTICIPANT = "participant"
    JUDGE = "judge"


class TaskStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_WORK = "in_work"
    REVIEW = "review"
    DONE = "done"
