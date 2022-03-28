from abc import ABC
from typing import Protocol, Tuple, Any, BinaryIO


class SizeLike(Protocol):
    def _size_(self) -> int:
        ...


class SizeLikeMixin:
    def _size_(self) -> int:
        raise NotImplementedError


class AlignLike(Protocol):
    def _align_(self) -> int:
        ...


class AlignLikeMixin:
    def _align_(self) -> int:
        raise NotImplementedError


class ArgLike(Protocol):
    def _args_(self) -> int:
        ...


class ArgLikeMixin:
    def _args_(self) -> int:
        raise NotImplementedError


class RepLike(Protocol):
    def _reps_(self) -> int:
        ...


class RepLikeMixin:
    def _reps_(self) -> int:
        raise NotImplementedError


class PackLike(Protocol):
    def pack(self, *args) -> bytes:
        ...

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        ...


class PackLikeMixin:
    def pack(self, *args) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        raise NotImplementedError


class BufferPackLike(Protocol):
    def pack_buffer(self,buffer:bytes,  *args, offset: int = 0) -> int:
        ...

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[Any, ...]:
        ...


class BufferPackLikeMixin:
    def pack_buffer(self, buffer:bytes, *args, offset: int = 0) -> int:
        raise NotImplementedError

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer, offset=offset)[1]


class StreamPackLike(Protocol):
    def pack_stream(self, stream:BinaryIO, *args) -> int:
        ...

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_stream(self, stream: BinaryIO) -> Tuple[Any, ...]:
        ...


class StreamPackLikeMixin:
    def pack_stream(self, stream: BinaryIO, *args) -> int:
        raise NotImplementedError

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def unpack_stream(self, stream: BinaryIO) -> Tuple[Any, ...]:
        return self._unpack_stream(stream)[1]


class PackAndSizeLike(PackLike, SizeLike):
    ...


class SubStructLike(AlignLike, BufferPackLike, StreamPackLike, PackLike, ArgLike, RepLike):
    ...


class SubStructLikeMixin(AlignLikeMixin, BufferPackLikeMixin, StreamPackLikeMixin, PackLikeMixin, ArgLikeMixin, RepLikeMixin, ABC):
    ...
