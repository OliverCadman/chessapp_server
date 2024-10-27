from enum import Enum


class Colours(Enum):
    BLACK = "black"
    WHITE = "white"
    RANDOM = "random"


class TimeControls(Enum):
    RAPID = 10
    BLITZ = 5
    SUPERBLITZ = 3
    BULLET = 1