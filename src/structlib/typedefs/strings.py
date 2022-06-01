from typing import Tuple

from structlib.abc_.packing import PrimitivePackableABC, IterPackableABC
from structlib.abc_.typedef import TypeDefSizableABC, TypeDefAlignableABC
from structlib.protocols.typedef import size_of, align_of
from structlib.typedefs.integer import IntegerDefinition
from structlib.utils import default_if_none, auto_pretty_repr


class StringBuffer(PrimitivePackableABC, IterPackableABC, TypeDefSizableABC, TypeDefAlignableABC):
    """
    Represents a fixed-buffer string.

    When packing; the string will be padded to fill the buffer
    When unpacking; padding is preserved
    """

    def prim_pack(self, arg: str) -> bytes:
        encoded = arg.encode(self._encoding)
        buf = bytearray(encoded)
        size = size_of(self)
        if len(buf) > size:
            raise
        elif len(buf) < size:
            buf.extend([0x00] * (size - len(buf)))
        return buf

    def unpack_prim(self, buffer: bytes) -> str:
        return buffer.decode(encoding=self._encoding)

    def iter_pack(self, *args: str) -> bytes:
        parts = [self.prim_pack(arg) for arg in args]
        empty = bytearray()
        return empty.join(parts)

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[str, ...]:
        size = size_of(self)
        partials = [buffer[i * size:(i + 1) * size] for i in range(iter_count)]
        unpacked = [self.unpack_prim(partial) for partial in partials]
        return tuple(unpacked)

    _DEFAULT_ENCODING = "ascii"

    def __init__(self, size: int, encoding: str = None, *, alignment: int = None):
        alignment = default_if_none(alignment, 1)
        TypeDefSizableABC.__init__(self, size)
        TypeDefAlignableABC.__init__(self, alignment)
        self._encoding = default_if_none(encoding, self._DEFAULT_ENCODING)

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, StringBuffer):
            return self.__typedef_alignment__ == other.__typedef_alignment__ and \
                   self.__typedef_native_size__ == other.__typedef_native_size__ and \
                   self._encoding == other._encoding
        else:
            return False

    def __str__(self):
        name = f"String [{size_of(self)}] ({self._encoding})"
        alignment = align_of(self)
        align_str = f" @ {alignment}" if alignment != 1 else ""
        return f"{name}{align_str}"

    def __repr__(self):
        return auto_pretty_repr(self)


class PascalString(PrimitivePackableABC, IterPackableABC, TypeDefAlignableABC):
    """
    Represents a var-buffer string.
    """

    def prim_pack(self, arg: str) -> bytes:
        encoded = arg.encode(self._encoding)

        size_packed = self._size_type.prim_pack(len(encoded))
        return size_packed.join() encoded

    def unpack_prim(self, buffer: bytes) -> str:
        return buffer.decode(encoding=self._encoding)

    def iter_pack(self, *args: str) -> bytes:
        parts = [self.prim_pack(arg) for arg in args]
        empty = bytearray()
        return empty.join(parts)

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[str, ...]:
        size = size_of(self)
        partials = [buffer[i * size:(i + 1) * size] for i in range(iter_count)]
        unpacked = [self.unpack_prim(partial) for partial in partials]
        return tuple(unpacked)

    _DEFAULT_ENCODING = "ascii"

    def __init__(self, size_type: IntegerDefinition, encoding: str = None, *, alignment: int = None):
        alignment = default_if_none(alignment, 1)
        TypeDefAlignableABC.__init__(self, alignment)
        self._encoding = default_if_none(encoding, self._DEFAULT_ENCODING)
        self._size_type = size_type

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(other, PascalString):
            return self.__typedef_alignment__ == other.__typedef_alignment__ and \
                   self._encoding == other._encoding
        else:
            return False

    def __str__(self):
        name = f"String [{size_of(self)}] ({self._encoding})"
        alignment = align_of(self)
        align_str = f" @ {alignment}" if alignment != 1 else ""
        return f"{name}{align_str}"

    def __repr__(self):
        return auto_pretty_repr(self)


class CStringBuffer(StringBuffer):
    """
    A Fixed string buffer that will auto-strip trailing `\0` when unpacking.

    Otherwise, it functions identically to StringBuffer.
    """

    def unpack_prim(self, buffer: bytes) -> str:
        return buffer.decode(encoding=self._encoding).rstrip("\0")

    def __str__(self):
        return "C" + super(CStringBuffer, self).__str__()

    def __repr__(self):
        return auto_pretty_repr(self)

# class _PascalString(SubStructLikeMixin):
#     def __init__(self, *, size_struct: PackAndSizeLike, align_as: int = None, encoding: str = None):
#         Alignable.__init__(self, align_as=align_as, default_align=size_of(size_struct))
#         ArgLikeMixin.__init__(self, args=1)
#         self._encoding = encoding
#         self._count_struct = size_struct
#
#     def unpack(self, buffer: bytes) -> Tuple[str, ...]:
#         count_size = size_of(self._count_struct)
#         count_buffer = buffer[:count_size]
#         data_size = self._count_struct.unpack(count_buffer)[0]
#         data = buffer[count_size:count_size + data_size]
#         decoded = data.decode(self._encoding)
#         if count_size + data_size < len(buffer):
#             raise NotImplementedError("Buffer Too Big!")
#         return tuple([decoded])
#
#     def pack(self, *args: str) -> bytes:
#         if len(args) != self._args_():
#             # TODO raise error
#             raise NotImplementedError
#         buffer = bytearray()
#         for arg in args:
#             b_str = arg.encode(self._encoding)
#             b_size = self._count_struct.pack(b_str)
#
#             buffer.extend(b_size)
#             buffer.extend(b_str)
#         return buffer
#
#     def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int = 0, origin: int = 0) -> int:
#         data = self.pack(*args)
#         return write_data_to_buffer(buffer, data, align_as=self._align_, offset=offset, origin=origin)
#
#     def _unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
#         size_read, size_buffer = read_data_from_buffer(buffer, self._count_struct._size_, align_as=self._align_, offset=offset, origin=origin)
#         size = self._count_struct.unpack(size_buffer)[0]
#
#         data_read, data_buffer = read_data_from_buffer(buffer, size, align_as=1, offset=offset + size_read, origin=origin)
#         decoded = data_buffer.decode(self._encoding)
#         return size_read + data_read, tuple([decoded])
#
#     def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = 0) -> int:
#         data = self.pack(*args)
#         return write_data_to_stream(stream, data, align_as=self._align_, origin=origin)
#
#     def _unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
#         size_read, size_buffer = read_data_from_stream(stream, self._count_struct._size_, align_as=self._align_, origin=origin)
#         size = self._count_struct.unpack(size_buffer)[0]
#         data_read, data_buffer = read_data_from_stream(stream, size, align_as=1, origin=origin)
#         decoded = data_buffer.decode(self._encoding)
#         return size_read + data_read, tuple([decoded])
#
#     def __str__(self):
#         return f"Pascal String [{self._count_struct}] ({self._encoding})"
#
#
# class PascalStringDefinition(_PascalString):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
#     class PascalString(_PascalString):
#         ...
#         # def __init__(self, args: int = 1, *, align_as: int = None, byteorder: str = None, size: int, signed: bool):
#         #     super().__init__(args=args, size=size, signed=signed, align=align_as, byteorder=byteorder)
#
#     #
#     def __init__(self, size_struct: PackAndSizeLike, *, encoding: str = None, align_as: int = None):
#         super().__init__(size_struct=size_struct, encoding=encoding, align_as=align_as)
#
#     def __call__(self, align_as: int = None, encoding: str = None) -> PascalString:
#         return self.PascalString(align_as=align_as or self._align_, size_struct=self._count_struct, encoding=encoding or self._encoding)
#
#     def __eq__(self, other):
#         # TODO, check 'same class' or 'sub class'
#         return self._count_struct == other._count_struct and self._encoding == other._encoding
#
#
# PString8 = PascalStringDefinition(integer.UInt8)
# PString16 = PascalStringDefinition(integer.UInt16)
# PString32 = PascalStringDefinition(integer.UInt32)
# PString64 = PascalStringDefinition(integer.UInt64)
# PString128 = PascalStringDefinition(integer.UInt128)
