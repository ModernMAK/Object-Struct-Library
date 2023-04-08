from __future__ import annotations

from typing import Tuple

from structlib.typedef import calculate_padding
from structlib.typeshed import WritableBuffer, ReadableBuffer


def write(
    buffer: WritableBuffer, data: bytes, alignment: int, offset: int, origin: int = 0
) -> int:
    """
    Writes data to a buffer, aligned to the `alignment boundaries` defined by alignment & origin

    :param buffer: A writable bytes-like buffer
    :param data: The raw bytes to write
    :param alignment: The alignment the bytes should
    :param offset: The offset from the origin to write to.
    :param origin: The origin to offset from. Also determines how
    :return:
    """

    data_size = len(data)

    prefix_padding = calculate_padding(alignment, offset)
    postfix_padding = calculate_padding(alignment, offset + prefix_padding + data_size)

    buffer_offset = origin + offset + prefix_padding
    postfix_offset = offset + prefix_padding + data_size

    apply_padding_to_buffer(buffer, prefix_padding, offset, origin)
    buffer[buffer_offset : buffer_offset + data_size] = data
    apply_padding_to_buffer(buffer, postfix_padding, postfix_offset, origin)

    return prefix_padding + data_size + postfix_padding


def pad_data_to_boundary(data: bytes, alignment: int) -> bytes:
    size = len(data)
    suffix_padding = calculate_padding(alignment, size)
    if suffix_padding > 0:
        suffix_padding_buf = create_padding_buffer(suffix_padding)
        data += suffix_padding_buf
    return data


def read(
    buffer: ReadableBuffer, data_size: int, alignment: int, offset: int, origin: int = 0
) -> Tuple[int, bytes]:
    prefix_padding = calculate_padding(alignment, offset)
    buffer_offset = origin + offset + prefix_padding
    postfix_offset = offset + prefix_padding + data_size
    postfix_padding = calculate_padding(alignment, postfix_offset)

    return (
        prefix_padding + data_size + postfix_padding,
        buffer[buffer_offset : buffer_offset + data_size],
    )


def create_padding_buffer(padding: int, pad_value: int = 0) -> bytes:
    return bytes([pad_value] * padding)


def apply_padding_to_buffer(
    buffer: WritableBuffer,
    padding: int,
    offset: int,
    origin: int = 0,
    pad_value: int = 0,
):
    # TypeError: 'bytes' object does not support item assignment ~ use bytearray instead
    pad_buffer = create_padding_buffer(padding, pad_value=pad_value)
    buffer[origin + offset : origin + offset + padding] = pad_buffer
