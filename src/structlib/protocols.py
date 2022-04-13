from abc import ABC
from typing import Protocol, Tuple, Any, BinaryIO


class SizeLike(Protocol):
    """
    Exposes the fixed size of a struct
    """

    def _size_(self) -> int:
        """
        The fixed size of the struct
        """
        ...


class SizeLikeMixin:
    def _size_(self) -> int:
        raise NotImplementedError


class AlignLike(Protocol):
    """
    Exposes the alignment of a struct
    """

    def _align_(self) -> int:
        """
        The alignment (in bytes) the struct will align to
        """
        ...


class AlignLikeMixin:
    def _align_(self) -> int:
        raise NotImplementedError


class ArgLike(Protocol):
    """
    The # of fields this structure holds
    """

    def _args_(self) -> int:
        """ The # of fields this structure expects """
        ...


class ArgLikeMixin:
    def _args_(self) -> int:
        raise NotImplementedError


class RepLike(Protocol):
    """
    The # of times this struct is repeated
    """

    def _reps_(self) -> int:
        ...


class RepLikeMixin:
    def _reps_(self) -> int:
        raise NotImplementedError


class PackLike(Protocol):
    """
    Exposes methods to pack/unpack a structure directly to/from bytes
    """

    def pack(self, *args: Any) -> bytes:
        """
        Packs the structure into it's byte format
        :param args: The arguments to pack.
        :raises: PackError: A special error occurred while packing.
        :raise: ArgTypeError: An argument was not of a valid type.
        """
        ...

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        """ 
        Unpacks the structure from it's byte format
        :raises: UnpackError: A special error occurred while unpacking.
        """
        ...


class PackLikeMixin:
    def pack(self, *args: Any) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        raise NotImplementedError


class BufferPackLike(Protocol):
    """
    Exposes methods to pack/unpack a structure to/from a byte buffer.
    """

    def pack_buffer(self, buffer: bytes, *args: Any, offset: int = 0, origin: int = 0) -> int:
        """
        Pack the arguments into the buffer.

        :param buffer: A byte-like buffer.
        :param args: The arguments to pack.
        :param offset: The offset into the buffer, relative to the origin.
        :param origin: The origin of the struct.
        :return: The number of bytes written to the buffer.
        :raises PackError: A special error occurred while packing.
        :raises ArgTypeError: An argument was not of a valid type.
        :code:

        """
        ...

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[Any, ...]:
        ...


class BufferPackLikeMixin:
    def pack_buffer(self, buffer: bytes, *args, offset: int = 0) -> int:
        raise NotImplementedError

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer, offset=offset)[1]


class StreamPackLike(Protocol):
    def pack_stream(self, stream: BinaryIO, *args, origin: int = 0) -> int:
        ...

    def _unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[Any, ...]:
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
