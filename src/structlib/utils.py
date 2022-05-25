from typing import Any

from structlib.typing_ import ReadableBuffer


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


def pretty_repr(repr, msg) -> str:
    """
    Inserts the msg into the 'repr' string between the first two words

    E.G.
    <MyClass (my message) object at 0x00112233>

    :param repr: The 'repr' string to parse and modify
    :param msg: The message to insert at the first 'space' character
    :return: Repr string with `msg` inserted at the first space.
    """
    pre, post = repr.split(" ", maxsplit=1)  # split before object
    return pre + f" ({msg}) " + post


def default_if_none(value: Any, default: Any) -> Any:
    """
    Returns default if value is None
    """
    return default if value is None else value
