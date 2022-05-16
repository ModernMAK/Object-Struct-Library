import math
import random
from io import BytesIO
from typing import Any, List, Union, Tuple

from structlib.protocols import PackLike, BufferPackLike, ReadableBuffer, StreamPackLike


def assert_array(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes], *, use_close: bool = False):
    if use_close:
        assert_array_close(l, r)
    else:
        assert_array_equal(l, r)


def assert_array_equal(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes]):
    assert len(l) == len(r), ("Len Mismatch:", len(l), "!=", len(r))
    for _ in range(len(l)):
        assert l[_] == r[_], ("Data Mismatch:", l[_], "!=", r[_], f"@{_}")


def assert_array_close(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes]):
    assert len(l) == len(r), ("Len Mismatch:", len(l), "!=", len(r))
    for _ in range(len(l)):
        assert math.isclose(l[_], r[_]), ("Data Mismatch:", l[_], "!~=", r[_], f"@{_}")


def assert_subarray(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes], _from: int, to: int, use_close: bool = False):
    if use_close:
        assert_subarray_close(l, r, _from, to)
    else:
        assert_subarray_equal(l, r, _from, to)


def assert_subarray_equal(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes], _from: int, to: int):
    assert _from <= to <= len(l), ("Len Mismatch (l):", _from, "<=", to, "<=", len(l))
    assert _from <= to <= len(r), ("Len Mismatch (r):", _from, "<=", to, "<=", len(r))
    for _ in range(_from, to):
        assert l[_] == r[_], ("Data Mismatch:", l[_], "!=", r[_], f"@{_}")


def assert_subarray_close(l: Union[List, Tuple, bytearray, bytes], r: Union[List, Tuple, bytearray, bytes], _from: int, to: int):
    assert _from <= to <= len(l), ("Len Mismatch (l):", _from, "<=", to, "<=", len(l))
    assert _from <= to <= len(r), ("Len Mismatch (r):", _from, "<=", to, "<=", len(r))
    for _ in range(_from, to):
        assert math.isclose(l[_], r[_]), ("Data Mismatch:", l[_], "!!=", r[_], f"@{_}")


def assert_pack_like(pack_like: PackLike, expected: ReadableBuffer, *args: Any, use_close: bool = False):
    packed = pack_like.pack(*args)
    assert_array(packed, expected, use_close=use_close)

    unpacked = pack_like.unpack(expected)
    assert_array(unpacked, args, use_close=use_close)


def assert_unpack_equal(l: PackLike, r: PackLike, buffer: bytes, use_close: bool = False):
    lp, rp = l.unpack(buffer), r.unpack(buffer)
    assert_array(lp, rp, use_close=use_close)


def assert_pack_equal(l: PackLike, r: PackLike, *args: Any, use_close: bool = False):
    lp, rp = l.pack(*args), r.pack(*args)
    assert_array(lp, rp, use_close=use_close)


def assert_buffer_pack_like(buffer_pack_like: BufferPackLike, expected: ReadableBuffer, *args: Any, offset: int = None, origin: int = None, use_close: bool = False):
    write_buffer = bytearray([0x00] * len(expected))
    written = buffer_pack_like.pack_buffer(write_buffer, *args, offset=offset, origin=origin)
    assert_subarray(write_buffer, expected, offset + origin, offset + origin + written - 1, use_close)  # -1 to make inclusive

    unpacked = buffer_pack_like.unpack_buffer(expected, offset=offset, origin=origin)
    assert_array(unpacked, args, use_close=use_close)


def assert_pack_buffer_equal(l: BufferPackLike, r: BufferPackLike, init_buffer: bytes, *args: Any, offset=None, origin=None, use_close: bool = False):
    lb, rb = bytearray(init_buffer), bytearray(init_buffer)  # create two separate writable buffers
    lp, rp = l.pack_buffer(lb, *args, offset=offset, origin=origin), r.pack_buffer(rb, *args, offset=offset, origin=origin)
    assert lp == rp
    assert_array(lb, rb, use_close=use_close)


def assert_unpack_buffer_equal(l: BufferPackLike, r: BufferPackLike, buffer: bytes, offset=None, origin=None, use_close: bool = False):
    lp, rp = l.unpack_buffer(buffer, offset=offset, origin=origin), r.unpack_buffer(buffer, offset=offset, origin=origin)
    assert_array(lp, rp, use_close=use_close)


def assert_stream_pack_like(stream_pack_like: StreamPackLike, expected: ReadableBuffer, *args: Any, offset: int = None, origin: int = None, use_close: bool = False):
    init_write_buffer = bytearray([0x00] * len(expected))
    with BytesIO(init_write_buffer) as write_stream:
        write_stream.seek(origin + offset)  # emulate offset
        written = stream_pack_like.pack_stream(write_stream, *args, origin=origin)
        write_stream.seek(0)
        write_buffer = write_stream.read()
        assert_subarray(write_buffer, expected, offset + origin, offset + origin + written - 1, use_close=use_close)  # -1 to make inclusive

    with BytesIO(expected) as read_stream:
        read_stream.seek(origin + offset)  # emulate offset
        unpacked = stream_pack_like.unpack_stream(read_stream, origin=origin)
        assert_array(unpacked, args, use_close=use_close)


def assert_pack_stream_equal(l: StreamPackLike, r: StreamPackLike, init_buffer: bytes, *args: Any, offset=None, origin=None, use_close: bool = False):
    with BytesIO(init_buffer) as ls:
        ls.seek(offset + origin)
        with BytesIO(init_buffer) as rs:
            rs.seek(offset + origin)

            lp, rp = l.pack_stream(ls, *args, origin=origin), r.pack_stream(rs, *args, origin=origin)
            assert lp == rp

            ls.seek(0)
            lb = ls.read()
            rs.seek(0)
            rb = rs.read()
            assert_array(lb, rb, use_close=use_close)


def assert_unpack_stream_equal(l: StreamPackLike, r: StreamPackLike, buffer: bytes, offset=None, origin=None, use_close: bool = False):
    with BytesIO(buffer) as ls:
        ls.seek(offset + origin)
        with BytesIO(buffer) as rs:
            rs.seek(offset + origin)
            lp, rp = l.unpack_stream(ls, origin=origin), r.unpack_stream(rs, origin=origin)
            assert_array(lp, rp, use_close=use_close)


def generate_random_chunks(chunk_size, chunk_count, seed: int):
    r = random.Random(seed)
    for _ in range(chunk_count):
        yield r.randbytes(chunk_size)
