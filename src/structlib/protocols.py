from abc import ABC
from typing import Protocol, Tuple, Any, BinaryIO, Union

# Non Exhaustive; most common would be bytes/bytearray

# Most types that allow my_copy = X[index] should be readable
from structlib.helper import default_if_none

ReadableBuffer = Union[bytes, bytearray]
# Most types that allow X[index] = new_value should be writable
WritableBuffer = Union[bytearray]


class SizeLike(Protocol):
    """
    Exposes the fixed size of a struct
    """

    @property
    def _size_(self) -> int:
        """
        The fixed size of the struct
        """
        ...


class SizeLikeMixin:
    def __init__(self, size: int):
        self.__size = size

    @property
    def _size_(self) -> int:
        return self.__size

    def __eq__(self, other) -> bool:
        if not isinstance(other, SizeLikeMixin):
            return False
        else:
            return self.__size == other.__size


class AlignLike(Protocol):
    """
    Exposes the alignment of a struct
    """

    @property
    def _align_(self) -> int:
        """
        The alignment (in bytes) the struct will align to
        """
        ...

    @_align_.setter
    def _align_(self, alignment: int) -> None:
        """
        Sets the alignment of this type.
        :param alignment: The desired alignment (in bytes) the struct will align to
        """
        ...


class AlignLikeMixin:
    def __init__(self, align_as: int, default_align: int = None):
        align_as = default_if_none(align_as, default_align)
        if align_as is None:
            raise ValueError("No alignment specified!")
        if align_as <= 0:
            raise ValueError("Alignment cannot be <= 0!")
        self.__alignment = align_as or default_align

    def __eq__(self, other) -> bool:
        if not isinstance(other, AlignLikeMixin):
            return False
        else:
            return self.__alignment == other.__alignment

    @property
    def _align_(self) -> int:
        return self.__alignment

    @_align_.setter
    def _align_(self, alignment: int) -> None:
        self.__alignment = alignment


class ArgLike(Protocol):
    """
    The # of fields this structure holds
    """

    def _args_(self) -> int:
        """ The # of fields this structure expects """
        ...


class ArgLikeMixin:
    def __init__(self, args: int):
        self.__args = args

    def _args_(self) -> int:
        return self.__args

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArgLikeMixin):
            return False
        else:
            return self.__args == other.__args


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

    def _unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        ...

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[Any, ...]:
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

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer, offset=offset, origin=origin)[1]


class StreamPackLike(Protocol):
    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = None) -> int:
        """
        Packs the structure into the stream

        :param stream:
        :param origin: The position to use in the stream as the start of the structure. None will use the current position in the stream.
        :return:
        """
        ...

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, Tuple[Any, ...]]:
        """
        Unpacks the structure from the stream,

        :param stream:
        :param origin: The position to use in the stream as the start of the structure. None will use the current position in the stream.
        :return:
        """
        ...

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[Any, ...]:
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

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[Any, ...]:
        return self._unpack_stream(stream, origin=origin)[1]


class PackAndSizeLike(PackLike, SizeLike):
    ...


class SubStructLike(AlignLike, BufferPackLike, StreamPackLike, PackLike, ArgLike):
    ...


class SubStructLikeMixin(AlignLikeMixin, BufferPackLikeMixin, StreamPackLikeMixin, PackLikeMixin, ArgLikeMixin, ABC):
    # def __init__(self, *pos_args, align_as: int = None, default_align:int = None, args:int = 1, **kwargs):
    #     super(AlignLikeMixin).__init__(align_as=align_as,default_align=default_align)
    #     super(ArgLikeMixin).__init__(args=args)
    ...
