from io import BytesIO
from struct import Struct
from typing import Tuple, Iterable, Union

from .core import StructObjHelper, StructObj, BufferApiType, BufferStream
from .error import StructVarBufferTooSmallError


class VarLenBytes(StructObjHelper):
    def __init__(self, size: Union[str, Struct, StructObj], repeat_size: int = 1):
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

    def _pack_into_stream(self, stream: BufferStream, *args, offset: int = None) -> int:
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

    def _pack_stream(self, stream: BufferStream, *args) -> int:
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

    def _unpack_stream(self, stream: BufferStream) -> Tuple[int, Tuple]:
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

    def _unpack_from_stream(self, stream: BufferStream, *, offset: int = None) -> Tuple[int, Tuple]:
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

    def _iter_unpack_stream(self, stream: BufferStream) -> Iterable[Tuple]:
        raise NotImplementedError
