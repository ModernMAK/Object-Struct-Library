from __future__ import annotations

from typing import Tuple, BinaryIO

from structlib.typing_ import WritableBuffer, ReadableBuffer
from structlib.utils import default_if_none


def create_padding_buffer(padding: int) -> bytes:
    return bytes([0x00]) * padding


def apply_padding_to_buffer(buffer: WritableBuffer, padding: int, offset: int, origin: int = 0):
    # TypeError: 'bytes' object does not support item assignment ~ use bytearray instead
    pad_buffer = create_padding_buffer(padding)
    buffer[origin + offset:origin + offset + padding] = pad_buffer


def write_data_to_buffer(buffer: WritableBuffer, data: bytes, alignment: int, offset: int, origin: int = 0) -> int:
    padding = calculate_padding(alignment, offset)
    apply_padding_to_buffer(buffer, padding, offset, origin)
    data_size = len(data)
    buffer[origin + offset + padding:origin + offset + padding + data_size] = data
    return padding + data_size


def read_data_from_buffer(buffer: ReadableBuffer, data_size: int, alignment: int, offset: int, origin: int = 0) -> Tuple[int, bytes]:
    padding = calculate_padding(alignment, offset)
    return padding + data_size, buffer[origin + offset + padding:origin + offset + padding + data_size]


def stream_offset_from_origin(stream: BinaryIO, origin: int):
    return stream.tell() - origin


def write_data_to_stream(stream: BinaryIO, data: bytes, alignment: int, origin: int = None) -> int:
    origin = default_if_none(origin, stream.tell())
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(alignment, offset)
    padding_buf = create_padding_buffer(padding)
    data_size = len(data)

    stream.write(padding_buf)
    stream.write(data)
    return padding + data_size


def read_data_from_stream(stream: BinaryIO, data_size: int, alignment: int, origin: int = None) -> Tuple[int, bytes]:
    origin = default_if_none(origin, stream.tell())
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(alignment, offset)
    _padding_buf = stream.read(padding)
    data = stream.read(data_size)
    return padding + data_size, data


def calculate_padding(alignment: int, size_or_offset: int) -> int:
    """
    Calculates the padding required to align a buffer to a boundary.

    If using a size; the padding is the padding required to align the type to the end of it's next `over aligned` boundary (suffix padding).
    If using an offset; the padding required to align the type to the start of its next `over aligned` boundary (prefix padding).

    :param alignment: The alignment in bytes. Any multiple of this value is an alignment boundary.
    :param size_or_offset: The size/offset to calculate padding for.
    :return: The padding required in terms of bytes.
    """
    bytes_from_boundary = size_or_offset % alignment
    if bytes_from_boundary != 0:
        return alignment - bytes_from_boundary
    else:
        return 0
