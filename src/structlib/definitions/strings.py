from typing import Tuple

from structlib.definitions.structure import _DepricatedPrimTypeStructDef
from structlib.packing.protocols import align_of, size_of
from structlib.utils import default_if_none


class StringBuffer(_DepricatedPrimTypeStructDef):
    """
    Represents a fixed-buffer string.

    When packing; the string will be padded to fill the buffer
    When unpacking; padding is preserved
    """
    _DEFAULT_ENCODING = "ascii"

    def __init__(self, size: int, align_as: int = None, encoding: str = None):
        # TODO how to align arrays?!
        #   Is it per element? Or to the first pointer?
        #       Unrelated; my understanding of size_of seems to be wrong `https://stackoverflow.com/questions/44023546/c-alignment-and-arrays`
        # FOR NOW, align to size and avoid the issue altogether (or the align specified)
        align = default_if_none(align_as, 1)
        super().__init__(size,align,self)
        self._encoding = default_if_none(encoding, self._DEFAULT_ENCODING)

    def __call__(self, size: int = None, align_as: int = None, encoding: str = None):
        # self.__class__ allows inheritors to use their class instead
        return self.__class__(size=default_if_none(size, size_of(self)), align_as=default_if_none(align_as, align_of(self)), encoding=default_if_none(encoding, self._encoding))

    def __eq__(self, other):
        return super().__eq__(other) and \
               self._encoding == other._encoding

    def _pack(self, *args: str) -> bytes:
        encoded = args[0].encode(self._encoding)
        buf = bytearray(encoded)
        size = size_of(self)
        if len(buf) > size:
            raise NotImplementedError
        elif len(buf) < size:
            buf.extend([0x00] * (size - len(buf)))
        return buf

    def _unpack(self, buffer: bytes) -> Tuple[str,...]:
        return buffer.decode(encoding=self._encoding),

    def __str__(self):
        return f"String [{size_of(self)}] ({self._encoding})"


class CStringBuffer(StringBuffer):
    """
    A Fixed string buffer that will auto-strip trailing `\0` when unpacking.

    Otherwise, it functions identically to StringBuffer
    """
    def _unpack(self, buffer: bytes) -> Tuple[str,...]:
        return buffer.decode(encoding=self._encoding).rstrip("\0"),

    def __str__(self):
        return f"CString [{size_of(self)}] ({self._encoding})"


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

if __name__ == "__main__":
    ...
