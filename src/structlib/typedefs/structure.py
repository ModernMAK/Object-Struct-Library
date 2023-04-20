from __future__ import annotations

from io import BytesIO
from typing import Any, Union, Tuple, BinaryIO, Type, Optional

from structlib.packing import PackableABC, ConstPackable

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


def _is_const(t):  # func to garuntee all checks are consistent
    return hasattr(t, "__typedef_const_packable__")


def _struct_zip(args, typedefs, *, expected_args: Optional[int] = None):
    if expected_args is not None and len(args) != expected_args:
        raise NotImplementedError  # TODO

    _args = iter(args)
    for typedef in typedefs:
        if _is_const(typedef):
            yield None, typedef, True
        else:
            yield next(_args), typedef, False


class Struct(PackableABC[Tuple], TypeDefSizableABC, TypeDefAlignableABC):
    @property
    def __typedef_annotation__(self) -> Type:
        return Tuple

    def _fixed_pack(self, args):
        written = 0
        buffer = bytearray(size_of(self))
        for arg, t, const in _struct_zip(args, self._types):
            packed = t.pack(arg) if not const else t.pack()
            # TODO; check if this fails when t is Struct because Tuple/List is wrapped
            written += bufferio.write(
                buffer, packed, align_of(t), written, origin=0
            )
        return buffer

    def _var_pack(self, args):
        with BytesIO() as stream:
            for arg, t, const in _struct_zip(args, self._types):
                packed = t.pack(arg) if not const else t.pack()
                # TODO; check if this fails when t is Struct because Tuple/List is wrapped
                streamio.write(stream, packed, align_of(t), origin=0)
            suffix_padding = bufferio.create_padding_buffer(
                calculate_padding(align_of(self), stream.tell())
            )
            stream.write(suffix_padding)
            stream.seek(0)
            return stream.read()

    def pack(self, args: Tuple) -> bytes:
        # TODO; packed result does not account for struct alignment
        #   EG. if the data is packed into 13 bytes, with an alignment of 4 on the struct, we should pad to 16 bytes
        #   THIS ONLY HAPPENS FOR NON-FIXED STRUCTURES!

        if self._fixed_size:
            return self._fixed_pack(args)
        else:
            return self._var_pack(args)

    def unpack(self, buffer: bytes) -> Tuple:
        total_read = 0
        results = []
        for t in self._types:
            read, result = t.unpack_from(buffer, offset=total_read, origin=0)
            if not _is_const(t):
                results.append(result)
            total_read += read
        return tuple(results)

    def _pack_buffer(
            self, buffer: WritableBuffer, args: Tuple, *, offset: int = 0, origin: int = 0
    ) -> int:
        packed = self.pack(args)
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def _pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        packed = self.pack(*args)
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

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
