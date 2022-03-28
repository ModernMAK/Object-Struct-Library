import sys
from enum import Enum


class ByteOrder(Enum):
    Little = "little"
    Big = "big"
    Network = Big  # `The form '!' represents the network byte order which is always big-endian as defined in IETF RFC 1700.` from "https://docs.python.org/3/library/struct.html#format-characters"
    Native = sys.byteorder
