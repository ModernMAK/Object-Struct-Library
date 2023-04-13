from __future__ import annotations

from io import BytesIO
from typing import Any, Union, Tuple, BinaryIO, Type

from structlib.packing import PackableABC

from structlib.typedef import (
    TypeDefAlignableABC,
    TypeDefSizableABC,
    TypeDefSizable,
    native_size_of,
    TypeDefAlignable,
    align_of,
    TypeDefSizableAndAlignable,
    size_of,
    calculate_padding,
)
from structlib import streamio, bufferio
from structlib.typedefs.array import AnyPackableTypeDef
from structlib.typeshed import WritableBuffer, ReadableBuffer


def _max_align_of(*types: TypeDefAlignable):
    alignments = []
    for _type in types:
        alignment = align_of(_type)
        if alignment is None:  # type is not complete!
            return None
        else:
            alignments.append(alignment)
    return max(alignments) if len(alignments) > 0 else None


def _combined_size(*types: TypeDefSizableAndAlignable):
    size = 0
    max_align = 1
    for t in types:
        t_align = align_of(t)
        max_align = max(max_align, t_align)
        t_prefix_pad = calculate_padding(t_align, size)
        t_native_size = native_size_of(t)
        t_postfix_pad = calculate_padding(t_align, t_native_size)
        size += t_prefix_pad + t_native_size + t_postfix_pad

    pad_to_max = calculate_padding(max_align, size)
    size += pad_to_max
    return size


class Struct(PackableABC[Tuple], TypeDefSizableABC, TypeDefAlignableABC):
    @property
    def __typedef_annotation__(self) -> Type:
        return Tuple

    def pack(self, args: Tuple) -> bytes:
        # TODO; packed result does not account for struct alignment
        #   EG. if the data is packed into 13 bytes, with an alignment of 4 on the struct, we should pad to 16 bytes
        #   THIS ONLY HAPPENS FOR NON-FIXED STRUCTURES!

        if self._fixed_size:
            written = 0
            buffer = bytearray(size_of(self))
            for arg, t in zip(args, self._types):
                packed = t.pack(arg=arg)
                # TODO; check if this fails when t is Struct because Tuple/List is wrapped
                written += bufferio.write(
                    buffer, packed, align_of(t), written, origin=0
                )
            return buffer
        else:
            with BytesIO() as stream:
                for arg, t in zip(args, self._types):
                    packed = t.pack(arg)
                    # TODO; check if this fails when t is Struct because Tuple/List is wrapped
                    streamio.write(stream, packed, align_of(t), origin=0)
                suffix_padding = bufferio.create_padding_buffer(
                    calculate_padding(align_of(self), stream.tell())
                )
                stream.write(suffix_padding)
                stream.seek(0)
                return stream.read()

    def unpack(self, buffer: bytes) -> Tuple:
        total_read = 0
        results = []
        for t in self._types:
            read, result = t._unpack_buffer(buffer, offset=total_read, origin=0)
            results.append(result)
            total_read += read
        return tuple(results)

    def _pack_buffer(
        self, buffer: WritableBuffer, args: Tuple, *, offset: int = 0, origin: int = 0
    ) -> int:
        packed = self.pack(args)
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def prim_unpack_buffer(
        self, buffer: ReadableBuffer, *, offset: int, origin: int
    ) -> Tuple[int, Tuple]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.unpack(packed)
        return read, unpacked

    def _pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        packed = self.pack(*args)
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def prim_unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Tuple]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.prim_unpack(packed)
        return read, unpacked

    def __init__(
        self,
        *types: Union[AnyPackableTypeDef, AnyPackableTypeDef],
        alignment: int = None,
    ):
        if alignment is None:
            alignment = _max_align_of(*types)
        self._fixed_size = all(isinstance(t, TypeDefSizable) for t in types)
        if self._fixed_size:
            try:
                size = _combined_size(*types)
                TypeDefSizableABC.__init__(self, size)
            except:  # TODO narrow exception
                # delattr(self, "__typedef_native_size__")
                ...
                raise
        else:
            ...
            # delattr(self, "__typedef_native_size__")

        TypeDefAlignableABC.__init__(self, alignment)
        self._types = types

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, Struct):
            return (
                self._fixed_size == other._fixed_size
                and self.__typedef_alignment__ == other.__typedef_alignment__
                and self.__typedef_native_size__ == other.__typedef_native_size__
                and self._types == other._types
            )
