from struct import Struct
from typing import BinaryIO, Tuple, Iterable, Union

from core import ObjStructField
from util import validate_pack_args, validate_typing, validate_buffer_size, validate_buffer_size_offset


class VarLenBytes(ObjStructField):
    def __init__(self, size: Union[str, Struct, ObjStructField], repeat_size: int = 1):
        if isinstance(size, str):
            size = Struct(size)

        self.__size_layout = size
        self.__repeat_size = repeat_size

    @property
    def format(self) -> str:
        raise TypeError("Var Len does not have a fixed format!")

    @property
    def size(self) -> int:
        raise TypeError("Var Len does not have a fixed size!")

    @property
    def min_size(self) -> int:
        return self.__size_layout.size * self.__repeat_size

    @property
    def args(self) -> int:
        return self.__repeat_size

    @property
    def is_var_size(self) -> bool:
        return True

    def pack(self, *args) -> bytes:
        validate_pack_args("pack", self.args, *args)
        validate_typing(self, args)
        buffer = bytearray()
        for a in args:
            l_buff = self.__size_layout.pack(len(a))
            buffer.extend(l_buff)
            buffer.extend(a)
        return buffer

    @classmethod
    def __pack_stream(cls, layout: Struct, buffer: BinaryIO, *args) -> int:
        written = 0
        for a in args:
            l_buff = layout.pack(len(a))
            buffer.write(l_buff)
            buffer.write(a)
            written += layout.size + len(a)
        return written

    def pack_into(self, buffer, *args, offset: int = 0) -> int:
        validate_pack_args("pack_into", self.args, *args)
        validate_buffer_size_offset("pack_into", self.min_size, buffer, offset)
        validate_typing(self, args)
        if not isinstance(buffer, BinaryIO):
            return_to = buffer.tell()
            buffer.seek(offset)
            written = self.__pack_stream(self.__size_layout, buffer, *args)
            buffer.seek(return_to)
            return written
        else:
            local_offset = 0
            for a in args:
                self.__size_layout.pack_into(buffer, local_offset + offset)
                local_offset += self.__size_layout.size
                buffer[local_offset:local_offset + len(a)] = a
                local_offset += len(a)
            return local_offset

    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        validate_pack_args("pack_stream", self.args, *args)
        validate_typing(self, args)
        return self.__pack_stream(self.__size_layout, buffer, *args)

    def __unpack_from(self, buffer, offset: int = 0) -> Tuple[int,Tuple]:
        results = []
        local_offset = offset
        for _ in range(self.__repeat_size):
            r_size = self.__size_layout.unpack_from(buffer, local_offset)[0]
            local_offset += self.__size_layout.size
            r = results[local_offset:local_offset + r_size]
            local_offset += r_size
            results.append(r)
        return local_offset, tuple(results)

    def __unpack_stream(self, buffer: BinaryIO) -> Tuple:
        results = []
        for _ in range(self.__repeat_size):
            r_size = self.__size_layout.unpack_stream(buffer)[0]
            r = buffer.read(r_size)
            results.append(r)
        return tuple(results)

    def unpack(self, buffer) -> Tuple:
        validate_buffer_size("unpack", self.min_size, buffer)
        if not isinstance(buffer, BinaryIO):
            return self.__unpack_stream(buffer)
        else:
            return self.__unpack_from(buffer)[1]

    def unpack_from(self, buffer, offset: int = 0) -> Tuple:
        validate_buffer_size_offset("unpack_from", self.min_size, buffer, offset)
        if not isinstance(buffer, BinaryIO):
            return_to = buffer.tell()
            buffer.seek(offset)
            r = self.__unpack_stream(buffer)
            buffer.seek(return_to)
            return r
        else:
            return self.__unpack_from(buffer, offset)[1]

    def var_unpack_from(self, buffer, offset: int = 0) -> Tuple[int, Tuple]:
        validate_buffer_size_offset("var_unpack_from", self.min_size, buffer, offset)
        if not isinstance(buffer, BinaryIO):
            return_to = buffer.tell()
            buffer.seek(offset)
            r = self.__unpack_stream(buffer)
            end = buffer.tell()
            buffer.seek(return_to)
            return end-offset, r
        else:
            return self.__unpack_from(buffer, offset)

    def unpack_stream(self, buffer: BinaryIO) -> Tuple:
        validate_buffer_size("unpack_stream", self.min_size, buffer)
        return self.__unpack_stream(buffer)

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        if not isinstance(buffer, BinaryIO):
            raise NotImplementedError
        else:
            raise NotImplementedError
