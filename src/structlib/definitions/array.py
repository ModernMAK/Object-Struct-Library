from typing import List, Tuple as _Tuple, Union, Type

from structlib.byteorder import ByteOrder
from structlib.definitions.structure import args2struct, T
from structlib.errors import ArgCountError
from structlib.packing.primitive import PrimitiveStructABC, WrappedPrimitiveStructABC
from structlib.packing.protocols import struct_definition, align_of, align_as, endian_of, BaseStructDefABC, endian_as, size_of, StructDefABC
from structlib.packing.structure import StructPackableABC
from structlib.utils import default_if_none, auto_pretty_repr


class FixedCollection(WrappedPrimitiveStructABC):
    @property
    def __struct_native_size__(self) -> int:  # Native size == size for arrays
        return size_of(self._backing) * self._args

    def __struct_align_as__(self: T, alignment: int) -> T:
        return self.__class__(self._args, align_as(self._backing, alignment))

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        return self.__class__(self._args, endian_as(self._backing, endian))

    def __init__(self, args: int, data_type: Union[Type[StructDefABC],StructDefABC], alignment: int = None, endian: ByteOrder = None):
        # FOR NOW, align to size and avoid the issue altogether (or the alignment specified)
        final_type = data_type
        if alignment is not None:
            final_type = align_as(data_type, alignment)
        if endian is not None:
            final_type = endian_as(data_type, endian)
        # size = size_of(final_type)
        # alignment = align_of(final_type)
        super().__init__(final_type, self)
        # self._data_type = final_type
        self._args = args

    def __call__(self, args: int = None, *, alignment: int = None, endian: ByteOrder = None):
        return self.__class__(default_if_none(args, self._args), self._backing, alignment=default_if_none(alignment, align_of(self)), endian=default_if_none(endian, endian_of(self)))

    def __eq__(self, other):
        if not isinstance(other, Array):
            return False
        else:
            return self._args == other._args and super().__eq__(other)

    def __str__(self):
        return f"Array[{self._args}] of `{self._backing}`"

    def __repr__(self):
        return auto_pretty_repr(self)

    def pack(self, arg: List) -> bytes:
        if len(arg) != self._args:
            raise ArgCountError(self.__class__.__name__, len(arg), self._args)
        t = struct_definition(self._backing)
        s = size_of(self)
        inner_s = size_of(self._backing)
        buf = bytearray(s)
        if isinstance(t, (PrimitiveStructABC, StructPackableABC)):
            t.iter_pack_buffer(buf, *arg, offset=0, origin=0)
        else:
            for i, d in enumerate(arg):
                buf[i * inner_s:(i + 1) * inner_s] = t.pack(*d)
        return buf

    def unpack(self, buffer: bytes) -> Union[List,_Tuple]:
        t = struct_definition(self._backing)
        s = size_of(self._backing)
        if isinstance(t, (PrimitiveStructABC, StructPackableABC)):
            _, results = t.iter_unpack_buffer(buffer, self._args, offset=0, origin=0)
        else:
            results = []
            for i in range(self._args):
                b = buffer[i * s:(i + 1) * s]
                args = t.unpack(b)
                unpacked = args2struct(t, args)
                results.append(unpacked)
        return results  # ensure result is list (iter_unpack_buffer returns tuple)


class Array(FixedCollection):
    def unpack(self, buffer: bytes) -> List:
        return list(super().unpack(buffer))


class Tuple(FixedCollection):
    def unpack(self, buffer: bytes) -> _Tuple:
        return tuple(super().unpack(buffer))
