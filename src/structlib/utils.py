from typing import Tuple, BinaryIO

from structlib.helper import default_if_none
from structlib.protocols import WritableBuffer, ReadableBuffer
from structlib.protocols_dir.size import SizeLike
from structlib.protocols_dir.align import AlignLike, align_of


# TODO
#   Mixins perform auto __init__, mine do not
#       Rename to be more appropriate ABC

# def align_of(alignable: AlignLike):
#     return alignable._align_
#
#
# def size_of(sizable: SizeLike):
#     return sizable._size_


def padding_of(alignable: AlignLike, offset: int) -> int:
    return calculate_padding(align_of(alignable), offset)


def calculate_padding(align_as: int, offset: int) -> int:
    bytes_from_align = offset % align_as
    if bytes_from_align != 0:
        return align_as - bytes_from_align
    else:
        return 0


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


def generate_chunks_from_buffer(buffer: ReadableBuffer, count: int, chunk_size: int, offset: int = 0):
    """
    Useful for splitting a buffer into fixed-sized chunks.
    :param buffer: The buffer to read from
    :param count: The amount of chunks to read
    :param chunk_size: The size (in bytes) of an individual chunk
    :param offset: The offset in the buffer to read from
    :return: A generator returning each chunk as bytes
    """
    for _ in range(count):
        yield buffer[offset + _ * chunk_size:offset + (_ + 1) * chunk_size]
