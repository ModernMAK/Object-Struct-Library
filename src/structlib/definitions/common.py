from typing import Tuple, BinaryIO

from structlib.protocols import SubStructLikeMixin, SizeLikeMixin


class Boolean(SubStructLikeMixin):
    TRUE = 0x01
    FALSE = 0x00

    def pack_buffer(self, buffer: bytes, *args: bool, offset: int = 0) -> int:
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset+data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin:int=0) -> Tuple[int, Tuple[bool, ...]]:
        read_size = 1
        data = buffer[origin+offset:origin+offset+read_size]
        return read_size, self.unpack(data)

    def pack_stream(self, stream: BinaryIO, *args: bool) -> int:
        return stream.write(self.pack(*args))

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple[bool, ...]]:
        read_size = self.__reps * self.__args
        data = stream.read(read_size)
        return read_size, self.unpack(data)

    def pack(self, *args: bool) -> bytes:
        # TODO error-checking
        return bytes([self.TRUE if a else self.FALSE for a in args])

    def unpack(self, buffer: bytes) -> Tuple[bool, ...]:
        # TODO error-checking
        return tuple([False if b == self.FALSE else True for b in buffer])

    def _args_(self) -> int:
        return self.__args

    def _reps_(self) -> int:
        return self.__reps

    def _align_(self) -> int:
        return 1


class Bytes(SubStructLikeMixin,SizeLikeMixin):
    def __init__(self, size:int):
        self.__size = size

    def pack_buffer(self, buffer: bytes, *args: bytes, offset: int = 0) -> int:
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset+data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[bool, ...]]:
        read_size = self.__reps * self.__args
        data = buffer[offset:offset+read_size]
        return read_size, self.unpack(data)

    def pack_stream(self, stream: BinaryIO, *args: bool) -> int:
        return stream.write(self.pack(*args))

    def _unpack_stream(self, stream: BinaryIO, *, origin:int = 0) -> Tuple[int, Tuple[bytes, ...]]:
        data = stream.read(read_size)
        return read_size, self.unpack(data)

    def pack(self, *args: bytes) -> bytes:
        # TODO error-checking
        return args[0]

    def unpack(self, buffer: bytes) -> Tuple[bytes, ...]:
        # TODO error-checking
        return tuple([buffer])


    def _size_(self) -> int:
        return self.__size

    def _args_(self) -> int:
        return 1

