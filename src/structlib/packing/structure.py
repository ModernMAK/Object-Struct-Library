from abc import ABC
from typing import Protocol, Any, Tuple, BinaryIO

from structlib.buffer_tools import write_data_to_buffer, read_data_from_buffer, write_data_to_stream, read_data_from_stream
from structlib.packing.protocols import align_of, StructDefABC, size_of

from structlib.typing_ import WritableBuffer, ReadableBuffer


class StructPackable(Protocol):
    def pack(self, *args: Any) -> bytes:
        ...

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        ...

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int, origin: int) -> int:
        ...

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        ...

    def unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Tuple[Any, ...]]:
        ...


class StructPackableABC(ABC):
    def pack(self, *args: Any) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int, origin: int) -> int:
        raise NotImplementedError

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        raise NotImplementedError

    def unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError


class StructIterPackable(Protocol):
    def iter_pack(self, *args: Tuple[Any, ...]) -> bytes:
        ...

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[Tuple[Any, ...], Any]:
        ...

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: Tuple[Any, ...], offset: int, origin: int) -> int:
        ...

    def iter_unpack_buffer(self, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        ...

    def iter_pack_stream(self, stream: BinaryIO, *args: Tuple[Any, ...], origin: int) -> int:
        ...

    def iter_unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        ...


class StructIterPackableABC(ABC):
    def iter_pack(self, *args: Tuple[Any, ...]) -> bytes:
        raise NotImplementedError

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[Tuple[Any, ...], Any]:
        raise NotImplementedError

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: Tuple[Any, ...], offset: int, origin: int) -> int:
        raise NotImplementedError

    def iter_unpack_buffer(self, buffer: ReadableBuffer, *, offset: int, origin: int) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        raise NotImplementedError

    def iter_pack_stream(self, stream: BinaryIO, *args: Tuple[Any, ...], origin: int) -> int:
        raise NotImplementedError

    def iter_unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        raise NotImplementedError


# Dumb name; interpreted as "Structure" using 'Structure-pack', as opposed to 'Dataclass-pack' or 'Primitive-pack'
class StructStructABC(StructPackableABC, StructIterPackableABC, StructDefABC, ABC):
    def pack(self, *args: Any) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        raise NotImplementedError

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(*args)
        alignment = align_of(self)
        return write_data_to_buffer(buffer, data, alignment, offset, origin)

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_buffer(buffer, size, alignment, offset=offset, origin=origin)
        data = self.unpack(raw)
        return read, data

    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = 0) -> int:
        alignment = align_of(self)
        data = self.pack(args)
        written, raw = write_data_to_stream(stream, data, alignment, origin=origin)
        return written

    def unpack_stream(self, stream: BinaryIO, *, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        size = size_of(self)
        alignment = align_of(self)
        read, raw = read_data_from_stream(stream, size, alignment, origin=origin)
        data = self.unpack(raw)
        return read, data

    def iter_pack(self, *args: Tuple[Any, ...]) -> bytes:
        buffer = bytearray()
        for arg in args:
            sub_buffer = self.pack(arg)
            buffer.extend(sub_buffer)
        return buffer

    def iter_unpack(self, buffer: bytes, iter_count: int) -> Tuple[Tuple[Any, ...], ...]:
        return self.iter_unpack_buffer(buffer, iter_count)[1]

    def iter_pack_buffer(self, buffer: WritableBuffer, *args: Tuple[Any, ...], offset: int = 0, origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_buffer(buffer, arg, offset=offset + written, origin=origin)
        return written

    def iter_unpack_buffer(self, buffer: ReadableBuffer, iter_count: int, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_buffer(buffer, offset=read + offset, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)

    def iter_pack_stream(self, stream: BinaryIO, *args: Tuple[Any, ...], origin: int = 0) -> int:
        written = 0
        for arg in args:
            written += self.pack_stream(stream, arg, origin=origin)
        return written

    def iter_unpack_stream(self, stream: BinaryIO, iter_count: int, *, origin: int = 0) -> Tuple[int, Tuple[Tuple[Any, ...], ...]]:
        read = 0
        items = []
        for _ in range(iter_count):
            r, item = self.unpack_stream(stream, origin=origin)
            read += r
            items.append(item)
        return read, tuple(items)
