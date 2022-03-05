from io import BytesIO
from mmap import mmap
from typing import Tuple, BinaryIO, Union, Any

BufferStream = Union[BytesIO, BinaryIO]  # TODO, better solution!?
BufferStreamTypes = (BytesIO, BinaryIO)
BufferApiType = Union[bytes, bytearray, mmap]
Buffer = Union[BufferStream, BufferApiType]
UnpackResult = Tuple[Any, ...]
UnpackLenResult = Tuple[int, UnpackResult]

__all__ = [
    "Buffer",
    "BufferStream",
    "BufferStreamTypes",
    "BufferApiType",
    "UnpackResult",
    "UnpackLenResult"
]