from abc import ABC, abstractmethod
from typing import (
    Tuple,
    BinaryIO,
    Any,
    runtime_checkable,
    Protocol,
    TypeVar,
    Type,
    Union,
)

from structlib.errors import PrettyNotImplementedError, ArgCountError, pretty_func_name
from structlib import streamio, bufferio
from structlib.typedef import TypeDefSizable, TypeDefAlignable, align_of, size_of
from structlib.typing_ import (
    WritableBuffer,
    ReadableBuffer,
    ReadableStream,
    WritableStream,
)


@runtime_checkable
class ConstPackable(Protocol):
    """
    A special packable for 'const' types; types that should know how to pack/unpack themselves without arguments.

    Padding / Constant Bytes / Data which should be ignored
    """

    @abstractmethod
    def const_pack(self) -> bytes:
        raise PrettyNotImplementedError(self, self.const_pack)

    @abstractmethod
    def const_unpack(self, buffer: bytes) -> None:
        raise PrettyNotImplementedError(self, self.const_unpack)

    @abstractmethod
    def const_pack_buffer(
            self, buffer: WritableBuffer, *, offset: int, origin: int
    ) -> int:
        raise PrettyNotImplementedError(self, self.const_pack_buffer)

    @abstractmethod
    def const_unpack_buffer(
            self, buffer: ReadableBuffer, *, offset: int, origin: int
    ) -> Tuple[int, None]:
        raise PrettyNotImplementedError(self, self.const_unpack_buffer)

    @abstractmethod
    def const_pack_stream(self, stream: WritableStream, *, origin: int) -> int:
        raise PrettyNotImplementedError(self, self.const_pack_stream)

    @abstractmethod
    def const_unpack_stream(
            self, stream: ReadableStream, *, origin: int
    ) -> Tuple[int, None]:
        raise PrettyNotImplementedError(self, self.const_unpack_stream)


class ConstPackableABC(ConstPackable, TypeDefSizable, TypeDefAlignable, ABC):
    """
    A ConstPackable which uses pack/unpack and a fixed size typedef to perform buffer/stream operations.
    """

    def const_pack_buffer(
            self, buffer: WritableBuffer, offset: int, origin: int
    ) -> int:
        packed = self.const_pack()
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def const_unpack_buffer(
            self, buffer: ReadableBuffer, *, offset: int, origin: int
    ) -> Tuple[int, Any]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.const_unpack(packed)
        return read, unpacked

    def const_pack_stream(self, stream: BinaryIO, *args: Any, origin: int) -> int:
        packed = self.const_pack()
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def const_unpack_stream(self, stream: BinaryIO, *, origin: int) -> Tuple[int, Any]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.const_unpack(packed)
        return read, unpacked


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


T = TypeVar("T")


@runtime_checkable
class PrimitivePackable(Protocol[T]):
    @abstractmethod
    def prim_pack(self, arg: T) -> bytes:
        raise PrettyNotImplementedError(self, self.prim_pack)

    @abstractmethod
    def unpack_prim(self, buffer: bytes) -> T:
        raise PrettyNotImplementedError(self, self.unpack_prim)

    @abstractmethod
    def prim_pack_buffer(
            self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0
    ) -> int:
        raise PrettyNotImplementedError(self, self.prim_pack_buffer)

    @abstractmethod
    def unpack_prim_buffer(
            self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0
    ) -> Tuple[int, T]:
        raise PrettyNotImplementedError(self, self.unpack_prim_buffer)

    @abstractmethod
    def prim_pack_stream(
            self, buffer: WritableStream, arg: T, *, origin: int = 0
    ) -> int:
        raise PrettyNotImplementedError(self, self.prim_pack_stream)

    @abstractmethod
    def unpack_prim_stream(
            self, buffer: ReadableStream, *, origin: int = 0
    ) -> Tuple[int, T]:
        raise PrettyNotImplementedError(self, self.unpack_prim_stream)


class PackableABC(PrimitivePackable[T], TypeDefSizable, TypeDefAlignable, ABC):
    """
    A Packable which uses pack/unpack to perform buffer/stream operations.
    """

    def prim_pack_buffer(
            self, buffer: WritableBuffer, arg: T, *, offset: int = 0, origin: int = 0
    ) -> int:
        packed = self.prim_pack(arg)
        alignment = align_of(self)
        return bufferio.write(buffer, packed, alignment, offset, origin)

    def unpack_prim_buffer(
            self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0
    ) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = bufferio.read(buffer, size, alignment, offset, origin)
        unpacked = self.unpack_prim(packed)
        return read, unpacked

    def prim_pack_stream(
            self, stream: WritableStream, arg: T, *, origin: int = 0
    ) -> int:
        packed = self.prim_pack(arg)
        alignment = align_of(self)
        return streamio.write(stream, packed, alignment, origin)

    def unpack_prim_stream(
            self, stream: ReadableStream, *, origin: int = 0
    ) -> Tuple[int, T]:
        size = size_of(self)
        alignment = align_of(self)
        read, packed = streamio.read(stream, size, alignment, origin)
        unpacked = self.unpack_prim(packed)
        return read, unpacked


@runtime_checkable
class Packable(Protocol):
    @abstractmethod
    def pack(self, args: Any) -> bytes:
        raise PrettyNotImplementedError(self, self.pack)

    @abstractmethod
    def unpack(self, buffer: bytes) -> Any:
        raise PrettyNotImplementedError(self, self.unpack)

    @abstractmethod
    def pack_buffer(
            self, buffer: WritableBuffer, args: Any, offset: int, origin: int
    ) -> int:
        raise PrettyNotImplementedError(self, self.pack_buffer)

    @abstractmethod
    def unpack_buffer(
            self, buffer: ReadableBuffer, *, offset: int, origin: int
    ) -> Tuple[int, Any]:
        raise PrettyNotImplementedError(self, self.unpack_buffer)

    @abstractmethod
    def pack_stream(self, stream: WritableStream, args: Any, origin: int) -> int:
        raise PrettyNotImplementedError(self, self.pack_stream)

    @abstractmethod
    def unpack_stream(self, stream: ReadableStream, *, origin: int) -> Tuple[int, Any]:
        raise PrettyNotImplementedError(self, self.unpack_stream)


TTuple = Tuple[T, ...]
DClass = TypeVar("DClass")
DClassType = Type[DClass]
DClassTuple = Tuple[DClass, ...]

EXP_PRIM_ARGS = 1


def PrettyTypeError(self, proto):
    return TypeError(
        f"`{self.__class__.__name__}` does not implement an explicit `{proto.__class__.__name__}` protocol!"
    )


AnyPackable = Union[PrimitivePackable]


@runtime_checkable
class ConstIterPackable(Protocol):
    @classmethod
    @abstractmethod
    def iter_const_pack(cls, *args: DClass) -> bytes:
        raise PrettyNotImplementedError(cls, cls.iter_const_pack)

    @classmethod
    @abstractmethod
    def iter_const_unpack(cls, buffer: bytes, iter_count: int) -> None:
        raise PrettyNotImplementedError(cls, cls.iter_const_unpack)

    @classmethod
    @abstractmethod
    def iter_const_pack_buffer(
            cls, buffer: WritableBuffer, *, offset: int, origin: int
    ) -> int:
        raise PrettyNotImplementedError(cls, cls.iter_const_pack_buffer)

    @classmethod
    @abstractmethod
    def iter_const_unpack_buffer(
            cls: DClassType,
            buffer: ReadableBuffer,
            iter_count: int,
            *,
            offset: int,
            origin: int,
    ) -> Tuple[int, None]:
        raise PrettyNotImplementedError(cls, cls.iter_dclass_unpack_buffer)

    @classmethod
    @abstractmethod
    def iter_const_pack_stream(cls, stream: WritableStream, *, origin: int) -> int:
        raise PrettyNotImplementedError(cls, cls.iter_const_pack_stream)

    @classmethod
    @abstractmethod
    def iter_const_unpack_stream(
            cls, stream: ReadableStream, iter_count: int, *, origin: int
    ) -> Tuple[int, None]:
        raise PrettyNotImplementedError(cls, cls.iter_const_unpack_stream)


def pack(self: AnyPackable, *args: Any) -> bytes:
    """
    Calls an appropriate 'Packable' implementation using the universal 'Packable' signature.

    The first Packable implementation found is used, and is checked in this order:
        Packable, StructPackable, PrimitivePackable, DataclassPackable

    Interpretation of args varies when using Struct, Primitive, Dataclass, or Packable.
        Packable: *args is not modified
        Struct: *args is not modified
        Primitive: only `args[0]` is used; raises ArgCountError if len(args) != 1
        Dataclass: `args[0]` is used IF specified; raises ArgCountError if len(args) not in [0,1]

    :param self: The `Packable` instance or class object
    :param args: The arguments to pass to the proper packable implementation
    :return:
    """
    arg_count = len(args)
    if isinstance(self, PrimitivePackable):
        if arg_count != EXP_PRIM_ARGS:
            raise ArgCountError(
                pretty_func_name(self, self.prim_pack), arg_count, EXP_PRIM_ARGS
            )
        return self.prim_pack(args[0])
    else:
        raise PrettyTypeError(self, PrimitivePackable)


def nested_pack(self: AnyPackable, args: Any) -> bytes:
    """
    A `safe` version of pack that will properly pack / unpack args when `parsing` args in a struct


    :param self: The `Packable` instance or class object
    :param args: The arguments to pass to the proper packable implementation
    :return:
    """
    if isinstance(self, PrimitivePackable):
        return self.prim_pack(args)
    else:
        raise PrettyTypeError(self, PrimitivePackable)


def unpack(self, buffer: bytes) -> Any:
    if isinstance(self, PrimitivePackable):
        return self.unpack_prim(buffer)
    else:
        raise PrettyTypeError(self, PrimitivePackable)


def pack_buffer(
        self, buffer: WritableBuffer, *args: Any, offset: int, origin: int
) -> int:
    arg_count = len(args)
    if isinstance(self, PrimitivePackable):
        if arg_count != EXP_PRIM_ARGS:
            raise ArgCountError(
                pretty_func_name(self, self.prim_pack_buffer), arg_count, EXP_PRIM_ARGS
            )
        return self.prim_pack_buffer(buffer, args[0], offset=offset, origin=origin)
    else:
        raise PrettyTypeError(self, PrimitivePackable)


def unpack_buffer(
        self, buffer: ReadableBuffer, *, offset: int, origin: int
) -> Tuple[int, Any]:
    if isinstance(self, PrimitivePackable):
        return self.unpack_prim_buffer(buffer, offset=offset, origin=origin)
    else:
        raise PrettyTypeError(self, Packable)


def pack_stream(self, stream: WritableStream, *args: Any, origin: int) -> int:
    arg_count = len(args)

    if isinstance(self, PrimitivePackable):
        if arg_count != EXP_PRIM_ARGS:
            raise ArgCountError(
                pretty_func_name(self, self.prim_pack_stream), arg_count, EXP_PRIM_ARGS
            )
        return self.prim_pack_stream(stream, args[0], origin=origin)
    else:
        raise PrettyTypeError(self, PrimitivePackable)


def unpack_stream(self, stream: ReadableStream, *, origin: int) -> Tuple[int, Any]:
    if isinstance(self, PrimitivePackable):
        return self.unpack_prim_stream(stream, origin=origin)
    else:
        raise PrettyTypeError(self, Packable)


def iter_pack(self, *args: Any) -> bytes:
    if isinstance(self, IterPackable):
        return self.iter_pack(*args)
    else:
        raise PrettyTypeError(self, IterPackable)


def iter_unpack(self, buffer: bytes, iter_count: int) -> Any:
    if isinstance(self, IterPackable):
        return self.iter_unpack(buffer, iter_count)
    else:
        raise PrettyTypeError(self, IterPackable)


def iter_pack_buffer(
        self, buffer: WritableBuffer, *args: Any, offset: int, origin: int
) -> int:
    if isinstance(self, IterPackable):
        return self.iter_pack_buffer(buffer, *args, offset=offset, origin=origin)
    else:
        raise PrettyTypeError(self, IterPackable)


def iter_unpack_buffer(
        self, buffer: ReadableBuffer, iter_count: int, *, offset: int, origin: int
) -> Tuple[int, Any]:
    if isinstance(self, IterPackable):
        return self.iter_unpack_buffer(buffer, iter_count, offset=offset, origin=origin)
    else:
        raise PrettyTypeError(self, IterPackable)


def iter_pack_stream(self, stream: WritableStream, *args: Any, origin: int) -> int:
    if isinstance(self, IterPackable):
        return self.iter_pack_stream(stream, *args, origin=origin)
    else:
        raise PrettyTypeError(self, IterPackable)


def iter_unpack_stream(
        self, stream: ReadableStream, iter_count: int, *, origin: int
) -> Tuple[int, Any]:
    if isinstance(self, IterPackable):
        return self.iter_unpack_stream(stream, iter_count, origin=origin)
    else:
        raise PrettyTypeError(self, IterPackable)
