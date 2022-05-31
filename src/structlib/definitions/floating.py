# Using IEEE_754
import struct

from structlib.byteorder import ByteOrder
from structlib.packing.protocols import align_of, endian_of, native_size_of
from structlib.packing.primitive import PrimitiveStructABC
from structlib.utils import default_if_none, pretty_str, auto_pretty_repr


class _Float(PrimitiveStructABC):
    """
    Structs organized by (bit_size, endian [literal])
    """
    INTERNAL_STRUCTS = {
        (16, "little"): struct.Struct("<e"),
        (16, "big"): struct.Struct(">e"),

        (32, "little"): struct.Struct("<f"),
        (32, "big"): struct.Struct(">f"),

        (64, "little"): struct.Struct("<d"),
        (64, "big"): struct.Struct(">d"),
    }

    def __struct_align_as__(self, alignment: int):
        return self.__class__(native_size_of(self) * 8, align_as=alignment, byteorder=endian_of(self))

    def __struct_endian_as__(self, endian: ByteOrder):
        return self.__class__(native_size_of(self) * 8, align_as=align_of(self), byteorder=endian)

    def __init__(self, bits: int, *, align_as: int = None, byteorder: str = None):
        alignment = default_if_none(align_as, bits // 8)
        super().__init__(bits // 8, alignment, self, endian=byteorder)
        self._internal = self.INTERNAL_STRUCTS[(bits, endian_of(self))]

    def __call__(self, *, align_as: int = None, byteorder: str = None):
        byte_size = native_size_of(self)
        alignment = default_if_none(align_as, align_of(self))
        byteorder = default_if_none(byteorder, endian_of(self))
        return _Float(byte_size * 8, align_as=alignment, byteorder=byteorder)

    def __str__(self):
        size = native_size_of(self) * 8
        endian = endian_of(self)
        alignment = align_of(self)
        return pretty_str(f"Float{size}", endian, alignment)

    def __repr__(self):
        return auto_pretty_repr(self)

    def unpack(self, buffer: bytes) -> float:
        native_size = native_size_of(self)
        data_buffer = buffer[0:native_size]
        return self._internal.unpack(data_buffer)[0]

    def pack(self, args: float) -> bytes:
        return self._internal.pack(args)


Float16 = _Float(16)
Float32 = _Float(32)
Float64 = _Float(64)
# Float16 = FloatDefinition(size=2, exponent_bits=5)
# Float32 = FloatDefinition(size=4, exponent_bits=8)
# Float64 = FloatDefinition(size=8, exponent_bits=11)
# Float128 = FloatDefinition(size=16, exponent_bits=15)
# Float256 = FloatDefinition(size=32, exponent_bits=19)
