from typing import Union, Protocol, Any, Tuple, BinaryIO
from dataclasses import dataclass

ReadableBuffer = Union[bytes, bytearray]
WritableBuffer = Union[bytearray]


@dataclass
class UnpackResult:
    bytes_read: int
    values: Tuple[Any]

    # Dataclass won't generate __init__ since we define one (according to docs)
    def __init__(self, read: int, *values: Any):
        self.bytes_read = read
        self.values = values

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]


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

    def unpack(self, buffer: bytes) -> UnpackResult:
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

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int = 0, origin: int = 0) -> int:
        """
        Pack the arguments into the buffer.
        :param buffer: A byte-like buffer.
        :param args: The arguments to pack.
        :param int offset: The offset into the buffer, relative to the origin.
        :param int origin: The origin of the struct.
        :return int: The number of bytes written to the buffer.
        :raises PackError: A special error occurred while packing.
        :raises ArgTypeError: An argument was not of a valid type.
        """
        ...

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> UnpackResult:
        """
        Unpacks arguments from the buffer.

        :param buffer: A byte-like buffer.
        :param int offset: The offset into the buffer, relative to the origin.
        :param int origin: The origin of the struct.
        :return Tuple[Any,...]: The unpacked arguments.
        """
        ...


class BufferPackLikeMixin:
    def pack_buffer(self, buffer: bytes, *args: Any, offset: int = 0, origin: int = 0) -> int:
        raise NotImplementedError

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> UnpackResult:
        raise NotImplementedError


class StreamPackLike(Protocol):
    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = None) -> int:
        """
        Packs the structure into the stream

        :param stream:
        :param origin: The position to use in the stream as the start of the structure. None will use the current position in the stream.
        :return:
        """
        ...

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> UnpackResult:
        """
        Unpacks the structure from the stream,

        :param stream:
        :param origin: The position to use in the stream as the start of the structure. None will use the current position in the stream.
        :return:
        """
        ...


class StreamPackLikeMixin:
    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = None) -> int:
        raise NotImplementedError

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> UnpackResult:
        raise NotImplementedError
