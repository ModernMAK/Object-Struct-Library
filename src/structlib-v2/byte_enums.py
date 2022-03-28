import sys

from enum import Enum, auto


class Endian(Enum):
    Little = "little"
    Big = "big"
    Network = Big
    Native = sys.byteorder


class Alignment(Enum):
    Unaligned = auto()
    Local = auto()
    Absolute = auto()
    Native = Local  #


class FormatSize(Enum):
    Native = auto()
    Standard = auto()
