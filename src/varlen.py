from io import BytesIO
from struct import Struct
from typing import BinaryIO, Tuple, Iterable, Union

from core import ObjStructHelper, ObjStruct, BufferApiType
from error import StructVarBufferTooSmallError


class VarLenBytes(ObjStructHelper):

    def __init__(self, size: Union[str, Struct, ObjStruct], repeat_size: int = 1):
        if isinstance(size, str):
            size = Struct(size)

        self.__size_layout = size
        self.__repeat_size = repeat_size

    @property
    def fixed_size(self) -> int:
        return self.__size_layout.fixed_size * self.__repeat_size

    @property
    def args(self) -> int:
        return self.__repeat_size

    @property
    def is_var_size(self) -> bool:
        return True

    def _pack(self, *args) -> bytes:
        with BytesIO() as stream:
            self._pack_stream(stream, *args)
            stream.seek(0)
            return stream.read()

    def _pack_into_stream(self, stream: BinaryIO, *args, offset: int = None) -> int:
        if offset is not None:
            return_to = stream.tell()
            stream.seek(offset)
            wrote = self._pack_stream(stream, *args)
            stream.seek(return_to)
        else:
            wrote = self._pack_stream(stream, *args)
            stream.seek(wrote, 1)
        return wrote

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        local_offset = 0
        for a in args:
            size = len(a)
            local_offset += self.__size_layout.pack_into(buffer, size, offset=offset + local_offset)
            buffer[offset + local_offset:offset + local_offset + size] = a[:]
            local_offset += size
        return local_offset

    def _pack_stream(self, stream: BinaryIO, *args) -> int:
        written = 0
        for a in args:
            size = len(a)
            size_bytes = self.__size_layout.pack(size)
            stream.write(size_bytes)
            stream.write(a)
            written += self.__size_layout.size + size
        return written

    def _unpack_buffer(self, buffer: BufferApiType) -> Tuple[int, Tuple]:
        return self._unpack_from_buffer(buffer)

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple]:
        total_read, results = 0, []
        for _ in range(self.args):
            read, (size,) = self.__size_layout.unpack_from_with_len(stream, total_read)
            r = stream.read(size)
            if len(r) != size:
                raise StructVarBufferTooSmallError("_unpack_stream", size, len(r))
            total_read += read + size
            results.append(r)
        return total_read, tuple(results)

    def _unpack_from_buffer(self, buffer: BufferApiType, *, offset: int = None) -> Tuple[int, Tuple]:
        offset = offset or 0
        total_read, results = 0, []
        for _ in range(self.args):
            read, (size,) = self.__size_layout.unpack_from_with_len(buffer, total_read + offset)
            r = buffer[offset + total_read:offset + total_read + size]
            total_read += read + size
            results.append(r)
        return total_read, tuple(results)

    def _unpack_from_stream(self, stream: BinaryIO, *, offset: int = None) -> Tuple[int, Tuple]:
        offset = offset or stream.tell()
        return_to = stream.tell()
        stream.seek(offset)
        total_read, results = 0, []
        for _ in range(self.args):
            read, (size,) = self.__size_layout.unpack_from_with_len(stream, total_read)
            r = stream.read(size)
            total_read += read + size
            results.append(r)
        stream.seek(return_to)
        return total_read, tuple(results)

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[Tuple]:
        raise NotImplementedError

    def _iter_unpack_stream(self, stream: BinaryIO) -> Iterable[Tuple]:
        raise NotImplementedError

    # @classmethod
    # def __pack_stream(cls, layout: Struct, buffer: BinaryIO, *args) -> int:
    #     written = 0
    #     for a in args:
    #         l_buff = layout.pack(len(a))
    #         buffer.write(l_buff)
    #         buffer.write(a)
    #         written += layout.size + len(a)
    #     return written
    #
    # def pack_into(self, buffer, *args, offset: int = 0) -> int:
    #     validate_pack_args("pack_into", self.args, *args)
    #     validate_buffer_size_offset("pack_into", self.min_size, buffer, offset)
    #     validate_typing(self, args)
    #     if not isinstance(buffer, BinaryIO):
    #         return_to = buffer.tell()
    #         buffer.seek(offset)
    #         written = self.__pack_stream(self.__size_layout, buffer, *args)
    #         buffer.seek(return_to)
    #         return written
    #     else:
    #         local_offset = 0
    #         for a in args:
    #             self.__size_layout.pack_into(buffer, local_offset + offset)
    #             local_offset += self.__size_layout.fixed_size
    #             buffer[local_offset:local_offset + len(a)] = a
    #             local_offset += len(a)
    #         return local_offset
    #
    # def pack_stream(self, buffer: BinaryIO, *args) -> int:
    #     validate_pack_args("pack_stream", self.args, *args)
    #     validate_typing(self, args)
    #     return self.__pack_stream(self.__size_layout, buffer, *args)
    #
    # def __unpack_from(self, buffer, offset: int = 0) -> Tuple[int,Tuple]:
    #     results = []
    #     local_offset = offset
    #     for _ in range(self.__repeat_size):
    #         r_size = self.__size_layout.unpack_from(buffer, local_offset)[0]
    #         local_offset += self.__size_layout.fixed_size
    #         r = results[local_offset:local_offset + r_size]
    #         local_offset += r_size
    #         results.append(r)
    #     return local_offset, tuple(results)
    #
    # def __unpack_stream(self, buffer: BinaryIO) -> Tuple:
    #     results = []
    #     for _ in range(self.__repeat_size):
    #         r_size = self.__size_layout.unpack_stream(buffer)[0]
    #         r = buffer.read(r_size)
    #         results.append(r)
    #     return tuple(results)
    #
    # def unpack(self, buffer) -> Tuple:
    #     validate_buffer_size("unpack", self.min_size, buffer)
    #     if not isinstance(buffer, BinaryIO):
    #         return self.__unpack_stream(buffer)
    #     else:
    #         return self.__unpack_from(buffer)[1]
    #
    # def unpack_from(self, buffer, offset: int = 0) -> Tuple:
    #     validate_buffer_size_offset("unpack_from", self.min_size, buffer, offset)
    #     if not isinstance(buffer, BinaryIO):
    #         return_to = buffer.tell()
    #         buffer.seek(offset)
    #         r = self.__unpack_stream(buffer)
    #         buffer.seek(return_to)
    #         return r
    #     else:
    #         return self.__unpack_from(buffer, offset)[1]
    #
    # def unpack_from_with_len(self, buffer, offset: int = 0) -> Tuple[int, Tuple]:
    #     validate_buffer_size_offset("var_unpack_from", self.min_size, buffer, offset)
    #     if not isinstance(buffer, BinaryIO):
    #         return_to = buffer.tell()
    #         buffer.seek(offset)
    #         r = self.__unpack_stream(buffer)
    #         end = buffer.tell()
    #         buffer.seek(return_to)
    #         return end-offset, r
    #     else:
    #         return self.__unpack_from(buffer, offset)
    #
    # def unpack_stream(self, buffer: BinaryIO) -> Tuple:
    #     validate_buffer_size("unpack_stream", self.min_size, buffer)
    #     return self.__unpack_stream(buffer)
    #
    # def iter_unpack(self, buffer) -> Iterable[Tuple]:
    #     if not isinstance(buffer, BinaryIO):
    #         raise NotImplementedError
    #     else:
    #         raise NotImplementedError
