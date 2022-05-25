from typing import List

from structlib.byteorder import ByteOrder
from structlib.definitions.structure import args2struct, T
from structlib.packing.protocols import struct_definition, align_of, align_as, endian_of, StructDefABC, endian_as, size_of
from structlib.errors import ArgCountError
from structlib.packing.structure import StructPackableABC
from structlib.packing.primitive import PrimitiveStructABC, WrappedPrimitiveStructABC
from structlib.utils import default_if_none, pretty_repr


class Array(WrappedPrimitiveStructABC):
    """
    An 'Array' only allows fixed-sized types, mimicking C++
    """

    @property
    def __struct_native_size__(self) -> int:  # Native size == size for arrays
        return size_of(self._backing) * self._args

    def __struct_align_as__(self: T, alignment: int) -> T:
        return self.__class__(self._args, align_as(self._backing, alignment))

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        return self.__class__(self._args, endian_as(self._backing, endian))

    def __init__(self, args: int, data_type: StructDefABC, alignment: int = None, endian: ByteOrder = None):
        # TODO how to align arrays?!
        #   Is it per element? Or to the first pointer?
        #       Unrelated; my understanding of size_of seems to be wrong `https://stackoverflow.com/questions/44023546/c-alignment-and-arrays`
        # FOR NOW, align to size and avoid the issue altogether (or the align specified)
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

    def __str__(self):
        return f"Array[{self._args}] of '{self._backing}'"

    def __eq__(self, other):
        if not isinstance(other, Array):
            return False
        else:
            return self._args == other._args and super().__eq__(other)

    def __repr__(self):
        repr = super().__repr__()
        msg = str(self)
        return pretty_repr(repr, msg)

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

    def unpack(self, buffer: bytes) -> List:
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
        return list(results)  # ensure result is list (iter_unpack_buffer returns tuple)
