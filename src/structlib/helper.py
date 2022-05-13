import sys
from typing import Any, Literal, Union

from structlib.enums import Endian


def default_if_none(value: Any, default: Any) -> Any:
    return default if value is None else value


ByteOrderLiteral = Literal["little", "big"]

ByteOrder = Union[Endian, ByteOrderLiteral]


def resolve_byteorder(byteorder: ByteOrder = None) -> ByteOrderLiteral:
    if not byteorder:
        return sys.byteorder
    elif isinstance(byteorder, Endian):
        return byteorder.value
    else:
        return byteorder
