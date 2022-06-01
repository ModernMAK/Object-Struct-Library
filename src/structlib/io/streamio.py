from __future__ import annotations

from typing import BinaryIO, Tuple

from structlib.io.bufferio import create_padding_buffer
from structlib.protocols.typedef import calculate_padding


def write(stream: BinaryIO, data: bytes, alignment: int, origin: int = 0) -> int:
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(alignment, offset)
    padding_buf = create_padding_buffer(padding)
    data_size = len(data)

    stream.write(padding_buf)
    stream.write(data)
    return padding + data_size


def read(stream: BinaryIO, data_size: int, alignment: int, origin: int = 0) -> Tuple[int, bytes]:
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(alignment, offset)
    _padding_buf = stream.read(padding)
    data = stream.read(data_size)
    return padding + data_size, data


def stream_offset_from_origin(stream: BinaryIO, origin: int):
    return stream.tell() - origin