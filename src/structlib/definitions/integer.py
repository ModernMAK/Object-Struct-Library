from __future__ import annotations

from structlib.byteorder import ByteOrder
from structlib.definitions.structure import get_type_buffer
from structlib.packing.primitive import PrimitiveStructABC
from structlib.packing.protocols import align_of, endian_of, native_size_of
from structlib.utils import default_if_none, pretty_str, auto_pretty_repr


class _Integer(PrimitiveStructABC):
    def unpack(self, buffer: bytes) -> int:
        # buffer may be bigger than native size! (If over-aligned)
        native_size = native_size_of(self)
        data_buffer = buffer[0:native_size]
        result = int.from_bytes(data_buffer, byteorder=endian_of(self), signed=self._signed)
        return result

    def pack(self, arg: int) -> bytes:
        native_size = native_size_of(self)
        data = arg.to_bytes(native_size, endian_of(self), signed=self._signed)
        return get_type_buffer(self, data)

    def __init__(self, *, size: int, signed: bool, align_as: int = None, byteorder: ByteOrder = None):
        super().__init__(size=size, align=default_if_none(align_as, size), _def=self, complete=True, endian=byteorder)
        self._signed = signed

    def __struct_align_as__(self, alignment: int):
        return self.__class__(size=native_size_of(self), signed=self._signed, align_as=alignment, byteorder=endian_of(self))

    def __struct_endian_as__(self, endian: ByteOrder):
        return self.__class__(size=native_size_of(self), signed=self._signed, align_as=align_of(self), byteorder=endian)

    def __eq__(self, other):
        if isinstance(other, _Integer):
            return super().__eq__(other) and \
                   self._signed == other._signed  # and \
            # self._byteorder == other._byteorder

    def __str__(self):
        name = 'Int' if self._signed else 'Uint'
        native_size = native_size_of(self)
        size = native_size * 8
        endian = endian_of(self)
        alignment = align_of(self)
        return pretty_str(f"{name}{size}",endian,alignment)

    def __repr__(self):
        return auto_pretty_repr(self)


class IntegerDefinition(_Integer):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    def __init__(self, size: int, signed: bool, *, align_as: int = None, byteorder: ByteOrder = None):
        if size < 1:
            raise NotImplementedError  # Todo raise an error
        super().__init__(size=size, signed=signed, align_as=align_as, byteorder=byteorder)

    def __call__(self, *, align_as: int = None, byteorder: ByteOrder = None) -> IntegerDefinition:
        return self.__class__(align_as=default_if_none(align_as, align_of(self)), byteorder=default_if_none(byteorder, endian_of(self)), size=native_size_of(self), signed=self._signed)


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
