import enum


class GlobalRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    ORGANIZATOR = "organizator"


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
