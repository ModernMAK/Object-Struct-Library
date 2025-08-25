from abc import ABC, abstractmethod
from types import NoneType
from typing import (
    Tuple,
    BinaryIO,
    Any,
    runtime_checkable,
    Protocol,
    TypeVar,
    Union,
    Optional,
)

from structlib import streamio, bufferio
from structlib.errors import PrettyNotImplementedError
from structlib.typedef import TypeDefSizable, TypeDefAlignable, align_of, size_of
from structlib.typeshed import (
    WritableBuffer,
    ReadableBuffer,
    ReadableStream,
    WritableStream,
)

T = TypeVar("T")

PackWritable = Union[WritableBuffer, WritableStream]
PackReadable = Union[ReadableBuffer, ReadableStream]


@runtime_checkable
class ConstPackable(Protocol):
    """
    A special packable for 'const' types; types that should know how to pack/unpack themselves without arguments.

    Padding / Constant Bytes / Reserved Fields

    Const Packable does NOT accept / return a result.
    """

    __typedef_const_packable__: NoneType = None

    @abstractmethod
    def pack(self) -> bytes:
        raise PrettyNotImplementedError(self, self.pack)

    @abstractmethod
    def unpack(self, buffer: bytes) -> None:
        raise PrettyNotImplementedError(self, self.unpack)

    @abstractmethod
    def pack_into(
            self,
            writable: PackWritable,
            *,
            offset: Optional[int] = None,
            origin: int = 0
    ) -> int:
        raise PrettyNotImplementedError(self, self.pack_into)

    @abstractmethod
    def unpack_from(
            self, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, None]:
        raise PrettyNotImplementedError(self, self.unpack_from)


class ConstPackableABC(ConstPackable, TypeDefSizable, TypeDefAlignable, ABC):
    """
    A ConstPackable which uses pack/unpack and a fixed size typedef to perform buffer/stream operations.
    """

    def pack_into(
            self,
            writable: PackWritable,
            # arg: T,
            *,
            offset: Optional[int] = None,
            origin: int = 0
    ) -> int:
        if isinstance(writable, WritableBuffer):
            return self._pack_buffer(writable, offset=offset or 0, origin=origin)
        else:
            if offset is not None:
                raise NotImplementedError(
                    "TODO: How do we handle offset being non-None for streams?"
                )  # TODO
            return self._pack_stream(writable, origin=origin)

    def unpack_from(
            self, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        if isinstance(readable, ReadableBuffer):
            return self._unpack_buffer(readable, offset=offset or 0, origin=origin)
        else:
            if offset is not None:
                raise NotImplementedError(
                    "TODO: How do we handle offset being non-None for streams?"
                )  # TODO
            return self._unpack_stream(readable, origin=origin)

    def _pack_buffer(
            self, buffer: WritableBuffer, *, offset: int = 0, origin: int = 0
    ) -> int:
        packed = self.pack()
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def _unpack_buffer(
            self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0
    ) -> Tuple[int, None]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.unpack(packed)
        return read, unpacked

    def _pack_stream(self, stream: WritableStream, *, origin: int = 0) -> int:
        packed = self.pack()
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def _unpack_stream(
            self, stream: ReadableStream, *, origin: int = 0
    ) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.unpack(packed)
        return read, unpacked


# TODO deprecate
@runtime_checkable
class IterPackable(Protocol):
    @abstractmethod
    def iter_pack(self, *args: Any) -> bytes:
        raise PrettyNotImplementedError(self, self.iter_pack)

    @abstractmethod
    def iter_unpack(self, buffer: bytes, iter_count: int) -> Any:
        raise PrettyNotImplementedError(self, self.iter_unpack)

    @abstractmethod
    def iter_pack_buffer(
            self, buffer: WritableBuffer, *args: Any, offset: int, origin: int
    ) -> int:
        raise PrettyNotImplementedError(self, self.iter_pack_buffer)

    @abstractmethod
    def iter_unpack_buffer(
            self, buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int
    ) -> Tuple[int, Any]:
        raise PrettyNotImplementedError(self, self.iter_unpack_buffer)

    @abstractmethod
    def iter_pack_stream(self, stream: WritableStream, *args: Any, origin: int) -> int:
        raise PrettyNotImplementedError(self, self.iter_pack_stream)

    @abstractmethod
    def iter_unpack_stream(
            self, stream: ReadableStream, iter_count: int, *, origin: int
    ) -> Tuple[int, Any]:
        raise PrettyNotImplementedError(self, self.iter_unpack_stream)


# TODO deprecate
class IterPackableABC(IterPackable, TypeDefSizable, TypeDefAlignable, ABC):
    """
    An IterPackable which uses iter_pack/iter_unpack to perform buffer/stream operations.
    """

    def iter_pack_buffer(
            self, buffer: WritableBuffer, *args: Any, offset: int, origin: int
    ) -> int:
        packed = self.iter_pack(*args)
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def iter_unpack_buffer(
            self, buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int
    ) -> Tuple[int, Any]:
        size = size_of(self) * iter_count
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.iter_unpack(packed, iter_count)
        return read, unpacked

    def iter_pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        packed = self.iter_pack(*args)
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def iter_unpack_stream(
            self, stream: BinaryIO, iter_count: int, *, origin: int
    ) -> Tuple[int, Any]:
        size = size_of(self) * iter_count
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.iter_unpack(packed, iter_count)
        return read, unpacked


@runtime_checkable
class Packable(Protocol[T]):
    @abstractmethod
    def pack(self, arg: T) -> bytes:
        raise PrettyNotImplementedError(self, self.pack)

    @abstractmethod
    def unpack(self, buffer: bytes) -> T:
        raise PrettyNotImplementedError(self, self.unpack)

    @abstractmethod
    def pack_into(
            self,
            writable: PackWritable,
            arg: T,
            *,
            offset: Optional[int] = None,
            origin: int = 0
    ) -> int:
        raise PrettyNotImplementedError(self, self.pack_into)

    @abstractmethod
    def unpack_from(
            self, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        raise PrettyNotImplementedError(self, self.unpack_from)


class PackableABC(Packable[T], TypeDefSizable, TypeDefAlignable, ABC):
    """
    A Packable which uses pack/unpack to perform buffer/stream operations.
    """

    def pack_into(
            self,
            writable: PackWritable,
            arg: T,
            *,
            offset: Optional[int] = None,
            origin: int = 0
    ) -> int:
        if isinstance(writable, WritableBuffer):
            return self._pack_buffer(writable, arg, offset=offset or 0, origin=origin)
        else:
            if offset is not None:
                raise NotImplementedError(
                    "TODO: How do we handle offset being non-None for streams?"
                )  # TODO
            return self._pack_stream(writable, arg, origin=origin)

    def unpack_from(
            self, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        if isinstance(readable, ReadableBuffer):
            return self._unpack_buffer(readable, offset=offset or 0, origin=origin)
        else:
            if offset is not None:
                raise NotImplementedError(
                    "TODO: How do we handle offset being non-None for streams?"
                )  # TODO
            return self._unpack_stream(readable, origin=origin)

    def _pack_buffer(
            self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0
    ) -> int:
        packed = self.pack(arg)
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def _unpack_buffer(
            self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0
    ) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.unpack(packed)
        return read, unpacked

    def _pack_stream(self, stream: WritableStream, arg: T, *, origin: int = 0) -> int:
        packed = self.pack(arg)
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def _unpack_stream(
            self, stream: ReadableStream, *, origin: int = 0
    ) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.unpack(packed)
        return read, unpacked
