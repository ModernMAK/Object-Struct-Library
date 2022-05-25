from abc import ABC
from typing import TypeVar, Protocol, Tuple, BinaryIO

from structlib.buffer_tools import write_data_to_buffer, read_data_from_buffer, write_data_to_stream, read_data_from_stream
from structlib.byteorder import ByteOrderLiteral, ByteOrder
from structlib.packing.protocols import struct_complete, align_of, align_as, endian_of, native_size_of, StructDef, StructDefABC, endian_as, size_of
from structlib.typing_ import WritableBuffer, ReadableBuffer

T = TypeVar("T")


class PrimitivePackable(Protocol):
    def pack(self, arg: T) -> bytes:
        ...

    def unpack(self, buffer: bytes) -> T:
        ...

    def pack_buffer(self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0) -> int:
        ...

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        ...

    def pack_stream(self, buffer: BinaryIO, arg: T, *, origin: int = 0) -> int:
        ...

    def unpack_stream(self, buffer: BinaryIO, *, origin: int = 0) -> Tuple[int, T]:
        ...


class PrimitivePackableABC(ABC):
    def pack(self, arg: T) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> T:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0) -> int:
        raise NotImplementedError

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        raise NotImplementedError

    def pack_stream(self, buffer: BinaryIO, arg: T, *, origin: int = 0) -> int:
        raise NotImplementedError

    def unpack_stream(self, buffer: BinaryIO, *, origin: int = 0) -> Tuple[int, T]:
        raise NotImplementedError


class PrimitiveIterPackable(Protocol):
    def iter_pack(self, *arg: T) -> bytes:
        ...

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        ...

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: T, offset: int = 0, origin: int = 0) -> int:
        ...

    def iter_unpack_buffer(self, buffer: ReadableBuffer, iter_count: int, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        ...

    def iter_pack_stream(self, buffer: BinaryIO, *args: T, origin: int = 0) -> int:
        ...

    def iter_unpack_stream(self, buffer: BinaryIO, iter_count: int, *, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        ...


class PrimitiveIterPackableABC(ABC):
    def iter_pack(self, *arg: T) -> bytes:
        raise NotImplementedError

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        raise NotImplementedError

    def iter_pack_buffer(self, buffer: WritableBuffer, *arg: T, offset: int = 0, origin: int = 0) -> int:
        raise NotImplementedError

    def iter_unpack_buffer(self, buffer: ReadableBuffer, iter_count: int, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        raise NotImplementedError

    def iter_pack_stream(self, buffer: BinaryIO, *arg: T, origin: int = 0) -> int:
        raise NotImplementedError

    def iter_unpack_stream(self, buffer: BinaryIO, iter_count: int, *, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        raise NotImplementedError


class PrimitiveStructDef(PrimitivePackable,PrimitiveIterPackable,StructDef,Protocol):
    ...


class PrimitiveStructABC(PrimitivePackableABC, PrimitiveIterPackableABC, StructDefABC, ABC):
    def pack(self, arg: T) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> T:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(arg)
        alignment = align_of(self)
        return write_data_to_buffer(buffer, data, alignment, offset, origin)

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_buffer(buffer, size, alignment, offset=offset, origin=origin)
        data = self.unpack(raw)
        return read, data

    def pack_stream(self, stream: BinaryIO, arg: T, *, origin: int = 0) -> int:
        alignment = align_of(self)
        data = self.pack(arg)
        written = write_data_to_stream(stream, data, alignment, origin=origin)
        return written

    def unpack_stream(self, stream: BinaryIO, *, origin: int = 0) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_stream(stream, size, alignment, origin=origin)
        data = self.unpack(raw)
        return read, data

    def iter_pack(self, *args: T) -> bytes:
        buffer = bytearray()
        for arg in args:
            sub_buffer = self.pack(arg)
            buffer.extend(sub_buffer)
        return buffer

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        return self.iter_unpack_buffer(buffer, iter_count)[1]

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: T, offset: int = 0, origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_buffer(buffer, arg, offset=offset + written, origin=origin)
        return written

    def iter_unpack_buffer(self, buffer: ReadableBuffer, iter_count: int, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_buffer(buffer, offset=read + offset, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)

    def iter_pack_stream(self, stream: BinaryIO, *args: T, origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_stream(stream, arg, origin=origin)
        return written

    def iter_unpack_stream(self, stream: BinaryIO, iter_count: int, *, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_stream(stream, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)


class WrappedPrimitiveStructABC(PrimitivePackableABC, PrimitiveIterPackableABC, ABC):
    def __init__(self, backing, _def=None):
        self.__struct_def__ = _def or self
        self._backing = backing

    def __eq__(self, other):
        if not isinstance(other,WrappedPrimitiveStructABC):
            return False
        return self._backing == other._backing

    @property
    def __struct_endian__(self) -> ByteOrderLiteral:
        return endian_of(self._backing)

    @property
    def __struct_native_size__(self) -> int:
        return native_size_of(self._backing)

    @property
    def __struct_alignment__(self) -> int:
        return align_of(self._backing)

    @property
    def __struct_complete__(self) -> bool:
        return struct_complete(self._backing)

    def pack(self, arg: T) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> T:
        raise NotImplementedError

    def __struct_align_as__(self: T, alignment: int) -> T:
        return self.__class__(align_as(self._backing, alignment), self.__struct_def__)

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        return self.__class__(endian_as(self._backing, endian), self.__struct_def__)

    def pack_buffer(self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(arg)
        alignment = align_of(self)
        return write_data_to_buffer(buffer, data, alignment, offset, origin)

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_buffer(buffer, size, alignment, offset=offset, origin=origin)
        data = self.unpack(raw)
        return read, data

    def pack_stream(self, stream: BinaryIO, arg: T, *, origin: int = 0) -> int:
        alignment = align_of(self)
        data = self.pack(arg)
        written = write_data_to_stream(stream, data, alignment, origin=origin)
        return written

    def unpack_stream(self, stream: BinaryIO, *, origin: int = 0) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_stream(stream, size, alignment, origin=origin)
        data = self.unpack(raw)
        return read, data

    def iter_pack(self, *args: T) -> bytes:
        buffer = bytearray()
        for arg in args:
            sub_buffer = self.pack(arg)
            buffer.extend(sub_buffer)
        return buffer

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[T, ...]:
        return self.iter_unpack_buffer(buffer, iter_count)[1]

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: T, offset: int = 0, origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_buffer(buffer, arg, offset=offset + written, origin=origin)
        return written

    def iter_unpack_buffer(self, buffer: ReadableBuffer, iter_count: int, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_buffer(buffer, offset=read + offset, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)

    def iter_pack_stream(self, stream: BinaryIO, *args: T, origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_stream(stream, arg, origin=origin)
        return written

    def iter_unpack_stream(self, stream: BinaryIO, iter_count: int, *, origin: int = 0) -> Tuple[int, Tuple[T, ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_stream(stream, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)
