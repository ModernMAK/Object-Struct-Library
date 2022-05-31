import sys
from enum import Enum
from typing import Literal, Union, Optional


class Endian(Enum):
    Little = "little"
    Big = "big"
    Network = Big  # `The form '!' represents the network byte order which is always big-endian as defined in IETF RFC 1700.` from "https://docs.python.org/3/library/struct.html#format-characters"
    Native = sys.byteorder  # Use the local system's byteorder # DEV NOTE; this seems susceptible to bugs (if it resolves at build time (package build) it's no longer using native but the build's native


ByteOrderLiteral = Literal["little", "big"]
ByteOrder = Union[Endian, ByteOrderLiteral]


def resolve_byteorder(byteorder: Optional[ByteOrder] = None) -> ByteOrderLiteral:
    """
    Resolves the argument to it's appropriate byteorder literal; 'little' or 'big'.

    A value of None will use the local system's byteorder.

    :param byteorder: The byteorder value to resolve; either an Endian enum, string literal ('little', 'big'), or None
    :return: The string literal form of the byteorder; 'little' or 'big'
    """
    if byteorder is None:
        return sys.byteorder
    elif isinstance(byteorder, Endian):
        return byteorder.value
    else:
        return byteorder


resolve_endian = resolve_byteorder  # Alias
