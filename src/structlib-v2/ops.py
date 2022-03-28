from typing import Tuple, Any, BinaryIO

from structlib.proto import CTypeLike, PackAndCTypeLike, TypeLike


def args(s: TypeLike) -> int:
    return s._args_()

def size_of(s: CTypeLike) -> int:
    return s._size_()


def alignment_of(s: CTypeLike) -> int:
    return s._align_()


def calculate_padding(align: int, index: int) -> int:
    return (align - (index % align)) % align


def padding_of(s: CTypeLike, index: int) -> int:
    alignment = alignment_of(s)
    return calculate_padding(alignment, index)


def create_padding_buffer(padding: int) -> bytes:
    return b"\x00" * padding


def pack_into(s: PackAndCTypeLike, buffer, offset: int, *args, aligned: bool = True) -> int:
    data = s.pack(*args)
    data_size = len(data)
    if not aligned:
        buffer[offset:offset + data_size] = data
        return data_size
    else:
        pad_size = padding_of(s, offset)
        padding = create_padding_buffer(pad_size)
        buffer[offset:offset + pad_size] = padding
        buffer[offset + pad_size:offset + pad_size + data_size] = data
        return data_size + pad_size


def _unpack_from(s: PackAndCTypeLike, buffer, offset: int, *, aligned: bool = True) -> Tuple[int, Tuple[Any, ...]]:
    data_size = size_of(s)
    if not aligned:
        data_buffer = buffer[offset:offset + data_size]
        args = s.unpack(data_buffer)
        return data_size, args
    else:
        pad_size = padding_of(s, offset)
        data_buffer = buffer[offset + pad_size:offset + pad_size + data_size]
        args = s.unpack(data_buffer)
        return data_size + pad_size, args


def unpack_from(s: PackAndCTypeLike, buffer, offset: int, *, aligned: bool = True) -> Tuple[Any, ...]:
    return _unpack_from(s, buffer, offset, aligned=aligned)[1]


def pack_stream(s: PackAndCTypeLike, stream: BinaryIO, *args, aligned: bool = True) -> int:
    data = s.pack(*args)
    if not aligned:
        return stream.write(data)
    else:
        offset = stream.tell()
        data_size = len(data)
        pad_size = padding_of(s, offset)
        padding = create_padding_buffer(pad_size)
        stream.write(padding)
        stream.write(data)
        return data_size + pad_size


def _unpack_stream(s: PackAndCTypeLike, stream: BinaryIO, *, aligned: bool = True) -> Tuple[int, Tuple[Any, ...]]:
    data_size = size_of(s)
    if not aligned:
        data_buffer = stream.read(data_size)
        args = s.unpack(data_buffer)
        return data_size, args
    else:
        offset = stream.tell()
        pad_size = padding_of(s, offset)
        _padding = stream.read(pad_size)
        data_buffer = stream.read(data_size)
        args = s.unpack(data_buffer)
        return data_size + pad_size, args


def unpack_stream(s: PackAndCTypeLike, stream:BinaryIO,  *, aligned: bool = True) -> Tuple[Any, ...]:
    return _unpack_stream(s, stream, aligned=aligned)[1]
