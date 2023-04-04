import sys
from typing import Literal, Optional

ByteOrder = Literal["little", "big"]

LittleEndian: Literal["little"] = "little"
BigEndian: Literal["big"] = "big"
NetworkEndian: ByteOrder = BigEndian
NativeEndian: ByteOrder = sys.byteorder


def resolve_byteorder(
    *byteorder: Optional[ByteOrder], default: ByteOrder = NativeEndian
) -> ByteOrder:
    """
    Will resolve to the first non-None byteorder, if all byteorder objects are None, default will be used.

    :param byteorder: List of ByteOrder (strings) in order of descending priority.
    :param default: The ByteOrder to use if all elements of the list are empty.
    :return: A non-null ByteOrder string.
    """
    for byteorder_mark in byteorder:
        if byteorder_mark is not None:
            return byteorder_mark
    return default
