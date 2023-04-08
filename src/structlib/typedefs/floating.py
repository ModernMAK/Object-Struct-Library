# Using IEEE_754
import struct
from typing import Tuple

from structlib.packing import IterPackableABC, PackableABC
from structlib.typedef import (
    TypeDefByteOrderABC,
    TypeDefAlignableABC,
    TypeDefSizableABC,
    native_size_of,
    align_of,
    size_of,
    byteorder_of,
)
from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.utils import default_if_none, pretty_str, auto_pretty_repr


class FloatDefinition(
    PackableABC,
    IterPackableABC,
    TypeDefSizableABC,
    TypeDefAlignableABC,
    TypeDefByteOrderABC,
):
    """
    Structs organized by (bit_size, byteorder [literal])
    """

    INTERNAL_STRUCTS = {
        (16, "little"): struct.Struct("<e"),
        (16, "big"): struct.Struct(">e"),
        (32, "little"): struct.Struct("<f"),
        (32, "big"): struct.Struct(">f"),
        (64, "little"): struct.Struct("<d"),
        (64, "big"): struct.Struct(">d"),
    }

    def __init__(
        self, bits: int, *, alignment: int = None, byteorder: ByteOrder = None
    ):
        native_size = (bits + 7) // 8
        alignment = default_if_none(alignment, native_size)
        byteorder = resolve_byteorder(byteorder)
        TypeDefSizableABC.__init__(self, native_size)
        TypeDefAlignableABC.__init__(self, alignment)
        TypeDefByteOrderABC.__init__(self, byteorder)
        self._internal = self.INTERNAL_STRUCTS[(bits, byteorder_of(self))]

    def __str__(self):
        size = native_size_of(self) * 8
        byteorder = byteorder_of(self)
        alignment = align_of(self)
        return pretty_str(f"Float{size}", byteorder, alignment)

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, FloatDefinition):
            return (
                self.__typedef_byteorder__ == other.__typedef_byteorder__
                and self.__typedef_alignment__ == other.__typedef_alignment__
                and self.__typedef_native_size__ == other.__typedef_native_size__
            )
        else:
            return False

    def __repr__(self):
        return auto_pretty_repr(self)

    def pack(self, arg: float) -> bytes:
        data = self._internal.pack(arg)
        buffer = bytearray(size_of(self))
        buffer[0 : len(data)] = data
        return buffer

    def unpack(self, buffer: bytes) -> float:
        data_buffer = buffer[0 : native_size_of(self)]
        return self._internal.unpack(data_buffer)[0]

    def iter_pack(self, *args: float) -> bytes:
        parts = [self.pack(arg) for arg in args]
        empty = bytearray()
        merged = empty.join(parts)
        return merged

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[float, ...]:
        size = size_of(self)
        partials = [buffer[i * size : (i + 1) * size] for i in range(iter_count)]
        results = [self.unpack(partial) for partial in partials]
        return tuple(results)


Float16 = FloatDefinition(16)
Float32 = FloatDefinition(32)
Float64 = FloatDefinition(64)
# Float16 = FloatDefinition(size=2, exponent_bits=5)
# Float32 = FloatDefinition(size=4, exponent_bits=8)
# Float64 = FloatDefinition(size=8, exponent_bits=11)
# Float128 = FloatDefinition(size=16, exponent_bits=15)
# Float256 = FloatDefinition(size=32, exponent_bits=19)
