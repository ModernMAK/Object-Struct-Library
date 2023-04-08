from copy import copy
from typing import List, Union, Type, Any, Tuple

from structlib.packing import (
    PackableABC,
    IterPackableABC,
    # _pack_buffer,
    # _unpack_buffer,
    # iter_pack,
    # iter_unpack,
)
from structlib.byteorder import ByteOrder
from structlib.typedef import (
    T,
)
from structlib.typedef import align_as, size_of, TypeDefByteOrder, byteorder_as
from structlib.utils import pretty_repr

AnyPackableTypeDef = Any  # TODO


class FixedCollection(
    PackableABC,
    IterPackableABC,
    # TypeDefSizable,
    # TypeDefAlignable,
    TypeDefByteOrder,
):
    @property
    def __typedef_native_size__(self) -> int:  # Native size == size for arrays
        return size_of(self._backing) * self._args

    @property
    def __typedef_alignment__(self) -> int:
        return self._backing.__typedef_alignment__

    @property
    def __typedef_byteorder__(self) -> int:
        return self._backing.__typedef_byteorder__

    def __typedef_align_as__(self, alignment: int):
        if self.__typedef_alignment__ != alignment:
            inst = copy(self)
            inst._backing = align_as(self._backing, alignment)
            return inst
        else:
            return self

    def __typedef_byteorder_as__(self, byteorder: ByteOrder):
        if self.__typedef_byteorder__ != byteorder:
            inst = copy(self)
            inst._backing = byteorder_as(self._backing, byteorder)
            return inst
        else:
            return self

    def __init__(
        self, args: int, data_type: Union[Type[AnyPackableTypeDef], AnyPackableTypeDef]
    ):
        self._backing = data_type
        self._args = args

    @classmethod
    def Unsized(
        cls: T, data_type: Union[Type[AnyPackableTypeDef], AnyPackableTypeDef]
    ) -> T:
        """
        Helper, returns an 'unsized' Array
        :param data_type:
        :return:
        """
        return cls(0, data_type)

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, Array):
            return self._args == other._args and self._backing == other._backing
        else:
            return False

    def __str__(self):
        return f"Array[{self._args}] of `{self._backing}`"

    def __repr__(self):
        repr = super().__repr__()
        msg = str(self)
        return pretty_repr(repr, msg)

    def pack(self, args: List) -> bytes:
        try:
            return self._backing.iter_pack(*args)
        except TypeError:
            size = size_of(self)
            buffer = bytearray(size)
            written = 0
            for arg in args:
                written += self._backing._pack_buffer(
                    self._backing, buffer, arg, offset=written, origin=0
                )
            return buffer

    def unpack(self, buffer: bytes) -> List:
        try:
            return self._backing.iter_unpack(buffer, self._args)
        except TypeError:
            total_read = 0
            results = []
            for _ in range(self._args):
                read, unpacked = self._backing._unpack_buffer(
                    buffer, offset=total_read, origin=0
                )
                total_read += read
                results.append(unpacked)
            return results

    def iter_pack(self, *args: List) -> bytes:
        parts = [self.pack(arg) for arg in args]
        empty = bytearray()
        return empty.join(parts)

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[List, ...]:
        size = size_of(self)
        partials = [buffer[i * size : (i + 1) * size] for i in range(iter_count)]
        parts = [self.unpack(partial) for partial in partials]
        return tuple(parts)


class Array(FixedCollection):
    ...


# It's too annoying when using typing.Tuple
# class Tuple(FixedCollection):
#     def unpack(self, buffer: bytes) -> _Tuple:
#         return tuple(super().unpack(buffer))
