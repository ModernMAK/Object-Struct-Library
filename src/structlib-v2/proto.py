from typing import Protocol, Any, Tuple


# Bad pythonic; but pseudo-dunder/magic felt right
class CTypeLike(Protocol):
    def _size_(self) -> int:
        ...

    def _align_(self) -> int:
        ...


class PackLike(Protocol):
    def pack(self, *args) -> bytes:
        ...

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        ...


class PackAndCTypeLike(PackLike, CTypeLike):
    ...


class BufferPackLike(Protocol):
    def pack_into(self, buffer, offset: int) -> int:
        ...

    def _unpack_from(self, buffer, offset: int) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_from(self, buffer, offset: int) -> Tuple[Any, ...]:
        ...


class StreamPackLike(Protocol):
    def pack_stream(self, stream) -> int:
        ...

    def _unpack_stream(self, stream) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_stream(self, stream) -> Tuple[Any, ...]:
        ...


class TypeLike(CTypeLike):
    def _args_(self) -> int:
        ...
