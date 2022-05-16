from typing import Tuple

from structlib.definitions.common import PrimitiveStructMixin
from structlib.errors import FixedBufferSizeError
from structlib.helper import default_if_none, ByteOrder, resolve_byteorder, ByteOrderLiteral
from structlib.protocols_dir.arg import ArgLikeMixin
from structlib.protocols_dir.size import SizeLikeMixin
from structlib.protocols_dir.align import Alignable


class _Integer(PrimitiveStructMixin):
    _typing_ = int

    def __init__(self, *, size: int, signed: bool, align_as: int = None, byteorder: ByteOrder = None):
        PrimitiveStructMixin.__init__(self, align_as=align_as, size=size)
        self._byteorder = resolve_byteorder(byteorder)
        self._signed = signed

    def __eq__(self, other) -> bool:
        if not isinstance(other, _Integer):
            return False
        else:
            return self._byteorder == other._byteorder and self._signed == other._signed and \
                   Alignable.__eq__(self, other) and \
                   SizeLikeMixin.__eq__(self, other) and \
                   ArgLikeMixin.__eq__(self, other)

    @property
    def byte_order(self) -> ByteOrderLiteral:
        return self._byteorder

    @property
    def signed(self) -> bool:
        return self._signed

    def _unpack(self, buffer: bytes) -> Tuple[int, ...]:
        result = int.from_bytes(buffer, byteorder=self._byteorder, signed=self._signed)
        return tuple([result])

    def _pack(self, *args: int) -> bytes:
        empty = bytearray()
        return empty.join([_.to_bytes(self._size_, self._byteorder, signed=self._signed) for _ in args])


class IntegerDefinition(_Integer):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    class Integer(_Integer):
        ...

    def __init__(self, size: int, signed: bool, *, align_as: int = None, byteorder: ByteOrder = None):
        if size < 1:
            raise NotImplementedError  # Todo raise an error
        super().__init__(size=size, signed=signed, align_as=align_as, byteorder=byteorder)

    def __call__(self, *, align_as: int = None, byteorder: ByteOrder = None) -> Integer:
        return self.Integer(align_as=default_if_none(align_as, self._align_), byteorder=default_if_none(byteorder, self.byte_order), size=self._size_, signed=self._signed)

    def __str__(self):
        # This should generate a 'Unique' string per equality, but not used for equality comparisons
        #   Repr will still use the class <object at id> syntax to clearly state they are different objects.
        signed = 'Int' if self._signed else 'Uint'
        size = self._size_ * 8
        endian = f'{self._byteorder[0]}e'  # HACK, _byteorder should be one of the literals 'l'ittle or 'b'ig
        align = f'-@{self._align_}' if self._align_ != self._size_ else ''
        return f"{signed}{size}-{endian}{align}"


Int8 = IntegerDefinition(1, True)
Int16 = IntegerDefinition(2, True)
Int32 = IntegerDefinition(4, True)
Int64 = IntegerDefinition(8, True)
Int128 = IntegerDefinition(16, True)

UInt8 = IntegerDefinition(1, False)
UInt16 = IntegerDefinition(2, False)
UInt32 = IntegerDefinition(4, False)
UInt64 = IntegerDefinition(8, False)
UInt128 = IntegerDefinition(16, False)

if __name__ == "__main__":
    AltInt8 = IntegerDefinition(1, True)
    AltInt8At2 = IntegerDefinition(1, True, align_as=2)
    print(Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, AltInt8, AltInt8At2)
    print(repr(Int8), "is", repr(AltInt8), ":", (Int8 is AltInt8))
    print(Int8, "==", AltInt8, ":", (Int8 == AltInt8))
    print(repr(Int8), "is", repr(AltInt8At2), ":", (Int8 is AltInt8At2))
    print(Int8, "==", AltInt8At2, ":", (Int8 == AltInt8At2))
