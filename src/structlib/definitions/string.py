from typing import Tuple, BinaryIO, Any

from structlib.definitions import integer
from structlib.protocols import PackAndSizeLike, SubStructLikeMixin, AlignLikeMixin, ArgLikeMixin
from structlib.utils import size_of, write_data_to_buffer, read_data_from_buffer, read_data_from_stream, write_data_to_stream


class _PascalString(SubStructLikeMixin):
    def __init__(self, *, size_struct: PackAndSizeLike, align_as: int = None, encoding: str = None):
        AlignLikeMixin.__init__(self,align_as=align_as, default_align=size_of(size_struct))
        ArgLikeMixin.__init__(self,args=1)
        self._encoding = encoding
        self._size_struct = size_struct

    def unpack(self, buffer: bytes) -> Tuple[str, ...]:
        size_size = self._size_struct._size_
        size_buffer = buffer[:size_size]
        data_size = self._size_struct.unpack(size_buffer)[0]
        data = buffer[size_size:size_size + data_size]
        decoded = data.decode(self._encoding)
        return tuple([decoded])

    def pack(self, *args: str) -> bytes:
        if len(args) != self._args_():
            # TODO raise error
            raise NotImplementedError
        buffer = bytearray()
        for arg in args:
            b_str = arg.encode(self._encoding)
            b_size = self._size_struct.pack(b_str)

            buffer.extend(b_size)
            buffer.extend(b_str)
        return buffer

    def pack_buffer(self, buffer: bytes, *args: Any, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=self._align_, offset=offset, origin=origin)

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        size_read, size_buffer = read_data_from_buffer(buffer, self._size_struct._size_(), align_as=self._align_, offset=offset, origin=origin)
        size = self._size_struct.unpack(size_buffer)[0]

        data_read, data_buffer = read_data_from_buffer(buffer, size, align_as=1, offset=offset + size_read, origin=origin)
        decoded = data_buffer.decode(self._encoding)
        return size_read + data_read, tuple([decoded])

    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = 0) -> int:
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=self._align_, origin=origin)

    def _unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        size_read, size_buffer = read_data_from_stream(stream, self._size_struct._size_(), align_as=self._align_, origin=origin)
        size = self._size_struct.unpack(size_buffer)[0]
        data_read, data_buffer = read_data_from_stream(stream, size, align_as=1, origin=origin)
        decoded = data_buffer.decode(self._encoding)
        return size_read + data_read, tuple([decoded])

    def __str__(self):
        return f"Pascal String [{self._size_struct}] ({self._encoding})"


class PascalStringDefinition(_PascalString):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    class PascalString(_PascalString):
        ...
        # def __init__(self, args: int = 1, *, align_as: int = None, byteorder: str = None, size: int, signed: bool):
        #     super().__init__(args=args, size=size, signed=signed, align=align_as, byteorder=byteorder)

    #
    def __init__(self, size_struct: PackAndSizeLike, *, encoding: str = None, align_as: int = None):
        super().__init__(size_struct=size_struct, encoding=encoding, align_as=align_as)

    def __call__(self, align_as: int = None, encoding: str = None) -> PascalString:
        return self.PascalString(align_as=align_as or self._align_, size_struct=self._size_struct, encoding=encoding or self._encoding)

    def __eq__(self, other):
        # TODO, check 'same class' or 'sub class'
        return self._size_struct == other._size_struct and self._encoding == other._encoding


PString8 = PascalStringDefinition(integer.UInt8)
PString16 = PascalStringDefinition(integer.UInt16)
PString32 = PascalStringDefinition(integer.UInt32)
PString64 = PascalStringDefinition(integer.UInt64)
PString128 = PascalStringDefinition(integer.UInt128)

if __name__ == "__main__":
    ...