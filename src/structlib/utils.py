from typing import Any

# TODO
#   Mixins perform auto __init__, mine do not
#       Rename to be more appropriate ABC
from structlib.protocols.pack import ReadableBuffer


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


def default_if_none(value: Any, default: Any) -> Any:
    return default if value is None else value
