from typing import Generic, Union, Type

from structlib.packing import ConstPackableABC, Packable
from structlib.typedef import TypeDefAnnotated, TypeDefAlignableABC, TypeDefSizableABC, TypeDefSizable, \
    TypeDefAlignable, T, align_as, annotation_of, align_of, native_size_of


class PaddingDefinition(ConstPackableABC, TypeDefSizableABC, TypeDefAlignableABC, TypeDefAnnotated):
    def pack(self) -> bytes:
        return self._padding_buffer

    def unpack(self, buffer: bytes) -> None:
        if buffer != self._padding_buffer:
            raise NotImplementedError
        return None

    def __init__(self, pad_char: bytes = b"\0", pad_size: int = 1, *, alignment: int = 1):
        self._padding_buffer = pad_char * pad_size
        TypeDefAlignableABC.__init__(self, alignment)
        TypeDefSizableABC.__init__(self, len(self._padding_buffer))


class ConstDefinition(ConstPackableABC, TypeDefSizable, TypeDefAlignable, TypeDefAnnotated, Generic[T]):
    def __init__(self, value: T, backing: Packable[T]):
        self._backing = backing
        self._const_val = value

    def pack(self) -> bytes:
        return self._backing.pack(self._const_val)

    def unpack(self, buffer: bytes) -> None:
        result = self._backing.unpack(buffer)
        if result != self._const_val:
            raise NotImplementedError
        return None

    def __typedef_align_as__(self: T, alignment: Union[TypeDefAlignable, int]) -> T:
        backing_aligned = align_as(self._backing, alignment)
        if backing_aligned != self._backing:
            return ConstDefinition(self._const_val, backing_aligned)
        else:
            return self

    @property
    def __typedef_annotation__(self) -> Type:
        return annotation_of(self._backing)

    @property
    def __typedef_alignment__(self) -> int:
        return align_of(self._backing)


    @property
    def __typedef_native_size__(self) -> int:
        return native_size_of(self._backing)


def Const(typedef, value) -> ConstDefinition:
    return ConstDefinition(value, typedef)
