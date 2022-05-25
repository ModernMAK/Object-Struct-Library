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


def write_data_to_buffer(buffer: WritableBuffer, data: bytes, align_as: int, offset: int, origin: int = 0) -> int:
    padding = calculate_padding(align_as, offset)
    apply_padding_to_buffer(buffer, padding, offset, origin)
    data_size = len(data)
    buffer[origin + offset + padding:origin + offset + padding + data_size] = data
    return padding + data_size


def read_data_from_buffer(buffer: ReadableBuffer, data_size: int, align_as: int, offset: int, origin: int = 0) -> Tuple[int, bytes]:
    padding = calculate_padding(align_as, offset)
    return padding + data_size, buffer[origin + offset + padding:origin + offset + padding + data_size]


def stream_offset_from_origin(stream: BinaryIO, origin: int):
    return stream.tell() - origin


def write_data_to_stream(stream: BinaryIO, data: bytes, align_as: int, origin: int = None) -> int:
    # TODO change all X or default to (default if _ is None)
    #   Even better, write a function which ONLY does None; or will alter false/0/falsy values
    origin = default_if_none(origin, stream.tell())
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(align_as, offset)
    padding_buf = create_padding_buffer(padding)
    data_size = len(data)

    stream.write(padding_buf)
    stream.write(data)
    return padding + data_size


def read_data_from_stream(stream: BinaryIO, data_size: int, align_as: int, origin: int = None) -> Tuple[int, bytes]:
    origin = default_if_none(origin, stream.tell())
    offset = stream_offset_from_origin(stream, origin)
    padding = calculate_padding(align_as, offset)
    _padding_buf = stream.read(padding)
    data = stream.read(data_size)
    return padding + data_size, data


def calculate_padding(alignment: int, size_or_offset: int) -> int:
    bytes_from_align = size_or_offset % alignment
    if bytes_from_align != 0:
        return alignment - bytes_from_align
    else:
        return 0
