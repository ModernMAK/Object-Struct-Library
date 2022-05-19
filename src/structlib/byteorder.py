import sys
from enum import Enum
from typing import Literal, Union


class Endian(Enum):
    Little = "little"
    Big = "big"
    Network = Big  # `The form '!' represents the network byte order which is always big-endian as defined in IETF RFC 1700.` from "https://docs.python.org/3/library/struct.html#format-characters"
    Native = sys.byteorder  # Use the local system's byteorder # DEV NOTE; this seems susceptible to bugs (if it resolves at build time (package build) it's no longer using native but the build's native


ByteOrderLiteral = Literal["little", "big"]

ByteOrder = Union[Endian, ByteOrderLiteral]


def resolve_byteorder(byteorder: ByteOrder = None) -> ByteOrderLiteral:
    if not byteorder:
        return sys.byteorder
    elif isinstance(byteorder, Endian):
        return byteorder.value
    else:
        return byteorder
