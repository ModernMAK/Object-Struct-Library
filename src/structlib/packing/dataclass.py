from abc import ABC
from typing import Protocol, Type, Tuple, BinaryIO, TypeVar

from structlib.buffer_tools import write_data_to_buffer, read_data_from_buffer, read_data_from_stream, write_data_to_stream
from structlib.packing.protocols import align_of, StructDef, BaseStructDefABC, size_of, StructDefABC
from structlib.typing_ import WritableBuffer, ReadableBuffer

T = TypeVar("T")


class DataclassPackable(Protocol):
    def pack(self) -> bytes:
        ...

    @classmethod
    def unpack(cls: T, buffer: bytes) -> T:
        ...

    def pack_buffer(self, buffer: WritableBuffer, *, offset: int, origin: int) -> int:
        ...

    @classmethod
    def unpack_buffer(cls: T, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, T]:
        ...

    def pack_stream(self, stream: BinaryIO, *, origin: int) -> int:
        ...

    @classmethod
    def unpack_stream(cls: T, stream: BinaryIO, *, origin: int) -> Tuple[int, T]:
        ...


class DataclassPackableABC(ABC):
    def pack(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def unpack(cls: T, buffer: bytes) -> T:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, *, offset: int, origin: int) -> int:
        raise NotImplementedError

    @classmethod
    def unpack_buffer(cls: T, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, T]:
        raise NotImplementedError

    def pack_stream(self, stream: BinaryIO, *, origin: int) -> int:
        raise NotImplementedError

    @classmethod
    def unpack_stream(cls: T, stream: BinaryIO, *, origin: int) -> Tuple[int, T]:
        raise NotImplementedError


class DataclassIterPackable(Protocol):
    @classmethod
    def iter_pack(cls: Type[T], *args: T) -> bytes:
        ...

    @classmethod
    def iter_unpack(cls: Type[T], buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        ...

    @classmethod
    def iter_pack_buffer(cls: Type[T], buffer: WritableBuffer, *args: T, offset: int, origin: int) -> int:
        ...

    @classmethod
    def iter_unpack_buffer(cls: Type[T], buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int) -> Tuple[int, T]:
        ...

    @classmethod
    def iter_pack_stream(cls: Type[T], stream: BinaryIO, *args: T, origin: int) -> int:
        ...

    @classmethod
    def iter_unpack_stream(cls: Type[T], stream: BinaryIO, iter_count: int, *, origin: int) -> Tuple[int, T]:
        ...


class DataclassIterPackableABC(ABC):
    @classmethod
    def iter_pack(cls: Type[T], *args: T) -> bytes:
        raise NotImplementedError

    @classmethod
    def iter_unpack(cls: Type[T], buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        raise NotImplementedError

    @classmethod
    def iter_pack_buffer(cls: Type[T], buffer: WritableBuffer, *args: T, offset: int, origin: int) -> int:
        raise NotImplementedError

    @classmethod
    def iter_unpack_buffer(cls: Type[T], buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int) -> Tuple[int, T]:
        raise NotImplementedError

    @classmethod
    def iter_pack_stream(cls: Type[T], stream: BinaryIO, *args: T, origin: int) -> int:
        raise NotImplementedError

    @classmethod
    def iter_unpack_stream(cls: Type[T], stream: BinaryIO, iter_count: int, *, origin: int) -> Tuple[int, T]:
        raise NotImplementedError


class DataclassStructDef(DataclassPackable, DataclassIterPackable, StructDef, Protocol):
    ...


class DataclassStructABC(DataclassPackableABC, DataclassIterPackableABC, StructDefABC, ABC):
    def pack(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def unpack(cls: T, buffer: bytes) -> T:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, *, offset: int, origin: int) -> int:
        data = self.pack()
        alignment = align_of(self)
        return write_data_to_buffer(buffer, data, alignment, offset, origin)

    @classmethod
    def unpack_buffer(cls: T, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, T]:
        size = size_of(cls)
        alignment = align_of(cls)
        read, raw = read_data_from_buffer(buffer, size, alignment, offset=offset, origin=origin)
        data = cls.unpack(raw)
        return read, data

    def pack_stream(self, stream: BinaryIO, *, origin: int) -> int:
        alignment = align_of(self)
        data = self.pack()
        written, raw = write_data_to_stream(stream, data, alignment, origin=origin)
        return written

    @classmethod
    def unpack_stream(cls: T, stream: BinaryIO, *, origin: int) -> Tuple[int, T]:
        size = size_of(cls)
        alignment = align_of(cls)
        read, raw = read_data_from_stream(stream, size, alignment, origin=origin)
        data = cls.unpack(raw)
        return read, data

    @classmethod
    def iter_pack(cls: Type[T], *args: T) -> bytes:
        buffer = bytearray()
        for arg in args:
            sub_buffer = arg.pack()
            buffer.extend(sub_buffer)
        return buffer

    @classmethod
    def iter_unpack(cls: Type[T], buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        return cls.iter_unpack_buffer(buffer, iter_count)[1]

    @classmethod
    def iter_pack_buffer(cls: Type[T], buffer: WritableBuffer, *args: T, offset: int, origin: int) -> int:
        written = 0
        for arg in args:
            written += cls.pack_buffer(buffer, arg, offset=offset + written, origin=origin)
        return written

    @classmethod
    def iter_unpack_buffer(cls: Type[T], buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int) -> Tuple[int, T]:
        total_bytes_read = 0
        results = []
        for _ in range(iter_count):
            bytes_read, item = cls.unpack_buffer(buffer, offset=total_bytes_read + offset, origin=origin)
            total_bytes_read += bytes_read
            results.append(item)
        return total_bytes_read, tuple(results)

    @classmethod
    def iter_pack_stream(cls: Type[T], stream: BinaryIO, *args: T, origin: int) -> int:
        written = 0
        for arg in args:
            written += cls.pack_stream(stream, arg, origin=origin)
        return written

    @classmethod
    def iter_unpack_stream(cls: Type[T], stream: BinaryIO, iter_count: int, *, origin: int) -> Tuple[int, T]:
        total_bytes_read = 0
        results = []
        for _ in range(iter_count):
            bytes_read, item = cls.unpack_stream(stream, origin=origin)
            total_bytes_read += bytes_read
            results.append(item)
        return total_bytes_read, tuple(results)
