from __future__ import annotations

from typing import Tuple

from structlib.protocols.typedef import calculate_padding
from structlib.typing_ import WritableBuffer, ReadableBuffer


def write(buffer: WritableBuffer, data: bytes, alignment: int, offset: int, origin: int = 0) -> int:
    """
    Writes data to a buffer, aligned to the `alignment boundaries` defined by alignment & origin

    :param buffer:
    :param data:
    :param alignment:
    :param offset:
    :param origin:
    :return:
    """
    padding = calculate_padding(alignment, offset)
    apply_padding_to_buffer(buffer, padding, offset, origin)
    data_size = len(data)
    buffer[origin + offset + padding:origin + offset + padding + data_size] = data
    return padding + data_size


def read(buffer: ReadableBuffer, data_size: int, alignment: int, offset: int, origin: int = 0) -> Tuple[int, bytes]:
    padding = calculate_padding(alignment, offset)
    return padding + data_size, buffer[origin + offset + padding:origin + offset + padding + data_size]


def create_padding_buffer(padding: int) -> bytes:
    return bytes([0x00] * padding)


def apply_padding_to_buffer(buffer: WritableBuffer, padding: int, offset: int, origin: int = 0):
    # TypeError: 'bytes' object does not support item assignment ~ use bytearray instead
    pad_buffer = create_padding_buffer(padding)
    buffer[origin + offset:origin + offset + padding] = pad_buffer