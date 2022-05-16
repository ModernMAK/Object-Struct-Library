from typing import Tuple

from structlib.definitions.common import PrimitiveStructMixin
from structlib.helper import default_if_none


class Boolean(PrimitiveStructMixin):
    _SIZE = 1
    TRUE = 0x01
    FALSE = 0x00

    def __init__(self, *, align_as: int = None):
        PrimitiveStructMixin.__init__(self, size=self._SIZE, align_as=default_if_none(align_as,self._SIZE))

    def _pack(self, *args: bool) -> bytes:
        return bytes([self.TRUE if a else self.FALSE for a in args])

    def _unpack(self, buffer: bytes) -> Tuple[bool, ...]:
        return tuple([False if b == self.FALSE else True for b in buffer])
