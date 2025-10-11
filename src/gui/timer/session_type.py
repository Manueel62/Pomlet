from enum import Enum, auto


class SessionType(Enum):
    WORK = auto()
    BREAK = auto()
    NONE = auto()
    LONG_BREAK = auto()
