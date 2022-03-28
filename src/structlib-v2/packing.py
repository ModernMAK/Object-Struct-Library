from io import BytesIO
from typing import BinaryIO, Union, Tuple

from structlib.byte_enums import Alignment

BinIO = Union[BinaryIO, BytesIO]


def calculate_padding(offset: int, alignment: int = 1, origin: int = 0) -> int:
    return (alignment - ((offset - origin) % alignment)) % alignment


def pack_fixed_buffer(buffer, data: bytes, offset: int = 0, alignment: int = 1, origin: int = 0, alignment_type: Alignment = Alignment.Native) -> int:
    data_size = len(data)
    if alignment_type == Alignment.Unaligned:
        buffer[offset:offset + data_size] = data
        return data_size
    else:
        if alignment_type == Alignment.Local:
            ...  # dont modify origin
        elif alignment_type == Alignment.Absolute:
            origin = 0
        else:
            raise ValueError(alignment_type)

    padding = calculate_padding(offset, alignment, origin)
    if padding == 0:
        buffer[offset:offset + data_size] = data
        return data_size
    else:
        buffer[offset:offset + padding] = b'\x00' * padding
        buffer[offset + padding:offset + padding + data_size] = data
        return padding + data_size


def unpack_fixed_buffer(buffer, data_size: int, offset: int = 0, alignment: int = 1, origin: int = 0, alignment_type: Alignment = Alignment.Native) -> Tuple[int,bytes]:
    if alignment_type == Alignment.Unaligned:
        return data_size, buffer[offset:offset + data_size]
    else:
        if alignment_type == Alignment.Local:
            ...  # dont modify origin
        elif alignment_type == Alignment.Absolute:
            origin = 0
        else:
            raise ValueError(alignment_type)

    padding = calculate_padding(offset, alignment, origin)
    if padding == 0:
        return data_size, buffer[offset: offset + data_size]
    else:
        return data_size+padding, buffer[offset + padding: offset + padding + data_size]


def pack_fixed_stream(stream: BinIO, data: bytes, offset: int = 0, alignment: int = 1, origin: int = 0, advance_stream: bool = True) -> int:
    raise NotImplementedError
    padding = calculate_padding(offset, alignment, origin)
    data_size = len(data)
    if padding != 0:
        stream.write(b'\x00' * padding)
    stream.write(data)
    if not advance_stream:
        stream.seek(-padding - data_size, 1)
    return padding + data_size


def unpack_fixed_stream(stream: BinIO, data_size: int, offset: int = 0, alignment: int = 1, origin: int = 0, advance_stream: bool = True) -> bytes:
    raise NotImplementedError
    padding = calculate_padding(offset, alignment, origin)
    if padding != 0:
        stream.seek(padding, 1)
    data = stream.read(data_size)
    if not advance_stream:
        stream.seek(-padding - data_size, 1)
    return data
