import struct
from io import BytesIO
from struct import Struct
from typing import Iterable, Tuple, List, Type

from structlib import definitions as std
from structlib.core import StructObj, MultiStruct
from structlib.packer import calculate_padding
from structlib.definitions.integer import Int16, Float


def test_standard_structs_against_builtin():
    CLASSES = std.struct_code2class.items()
    DATA = {
        "x": None,
        "c": b"\xea",  # It's in the game
        "s": "E".encode("ascii"),
        "?": False,
        "b": -1,
        "B": (2 ** 8 - 1),
        "h": (-1),
        "H": (2 ** 16 - 1),
        "i": (-1),
        "I": (2 ** 32 - 1),
        "l": (-1),
        "L": (2 ** 32 - 1),
        "q": (-1),
        "Q": (2 ** 64 - 1),
        "n": (-1),
        "N": (2 ** 64 - 1),
        "e": 1.234375,  # as close to 1.234 as half allows
        "f": 1.2339999675750732,  # as close to 1.234 as float allows
        "d": 1.23456789,
        # "p": b"\x01\x00", # IDK how this works, so I don't cover it; sorry
        "P": 1234567890,  # unsigned i guess?
    }
    for code, c in CLASSES:
        i = c()  # create instance
        # assert i.format == c.format
        assert i.args == c.args
        assert i.fixed_size == c.fixed_size
        # assert i.byte_flags == c.byte_flags
        if code in ['p']:  # not supported
            continue
        d = DATA[code]
        if d is None:
            i_dp, c_dp = i.pack(), c.pack()
        else:
            i_dp, c_dp = i.pack(d), c.pack(d)
        assert i_dp == c_dp
        i_du, c_du = i.unpack(i_dp), c.unpack(c_dp)
        assert i_du == c_du
        if d is None:
            assert i_du == ()
            assert c_du == ()
        else:
            assert i_du[0] == d
            assert c_du[0] == d

        struct_ = Struct(code)
        if d is None:
            struct__dp = struct_.pack()
        else:
            struct__dp = struct_.pack(d)
        assert i_dp == struct__dp
        assert c_dp == struct__dp

        struct_i_du, struct_c_du = i.unpack(i_dp), c.unpack(c_dp)
        assert struct_i_du == struct_c_du
        if d is None:
            assert struct_i_du == ()
            assert struct_c_du == ()
        else:
            assert struct_i_du[0] == d
            assert struct_c_du[0] == d


def build_offset_buffer(expected: bytes, offset: int = 1) -> Tuple[bytes, bytes]:
    e, w = bytearray(b"\x00" * offset), bytearray(b"\x00" * offset)
    e.extend(expected)
    w.extend(b"\x00" * len(expected))
    return e, w


def build_iter_buffer(expected: bytes, repeat: int = 2, alignment:int = None) -> bytes:
    w = bytearray()
    for _ in range(repeat):
        if alignment is not None:
            pad = calculate_padding(len(w),alignment)
            w.extend(b'\x00' * pad)
        w.extend(expected)
    return w


def run_test_with_data(obj: StructObj, data: Iterable[Tuple[Tuple, bytes, Tuple]], offsets: List[int] = None):
    offsets = offsets or [1]
    for test_args, expected_buffer, expected_result in data:
        # PACK
        buffer = obj.pack(*test_args)
        assert buffer == expected_buffer, "pack"

        for offset in offsets:
            # TEST BUFFER
            expected, writable = build_offset_buffer(expected_buffer, offset=offset)
            w = obj.pack_into(writable, *test_args, offset=offset)
            assert w == len(expected) - offset, "pack_into (buffer) size" + f" {obj}"
            assert expected == writable, "pack_into (buffer) data"

            # TEST STREAM
            expected, writable = build_offset_buffer(expected_buffer, offset=offset)
            with BytesIO(writable) as wrt_stream:
                w = obj.pack_into(wrt_stream, *test_args, offset=offset)
                wrt_stream.seek(0)
                writable = wrt_stream.read()
                assert w == len(expected) - offset, "pack_into (stream)"
                assert expected == writable, "pack_into (stream)"

        with BytesIO() as wrt_stream:
            w = obj.pack_stream(wrt_stream, *test_args)
            wrt_stream.seek(0)
            buffer = wrt_stream.read()
            assert w == len(buffer), "pack_stream"
            assert buffer == expected_buffer, "pack_stream"

        # Unpack BUFFER
        r = obj.unpack(expected_buffer)
        assert r == expected_result, "unpack (buffer)"
        read, r = obj.unpack_with_len(expected_buffer)
        assert read == len(expected_buffer), "unpack_with_len (buffer)"
        assert r == expected_result, "unpack_with_len (buffer)"
        # Unpack STREAM
        with BytesIO(expected_buffer) as str_buffer:
            r = obj.unpack(str_buffer)
            assert r == expected_result, "unpack (stream)"
            str_buffer.seek(0)
            read, r = obj.unpack_with_len(str_buffer)
            assert read == len(expected_buffer), "unpack_with_len (stream)"
            assert r == expected_result, "unpack_with_len (stream)"

        for offset in offsets:
            # TEST BUFFER
            expected, _ = build_offset_buffer(expected_buffer, offset=offset)
            r = obj.unpack_from(expected, offset=offset)
            assert r == expected_result, "unpack_from (buffer)"
            read, r = obj.unpack_from_with_len(expected, offset=offset)
            assert r == expected_result, "unpack_from_with_len (buffer)"
            assert read == len(expected_buffer), "unpack_from_with_len (buffer)"

            # TEST STREAM
            expected, _ = build_offset_buffer(expected_buffer, offset=offset)
            with BytesIO(expected) as wrt_stream:
                r = obj.unpack_from(expected, offset=offset)
                assert r == expected_result, "unpack_from (stream)"
                wrt_stream.seek(0)
                read, r = obj.unpack_from_with_len(expected, offset=offset)
                assert r == expected_result, "unpack_from_with_len (stream)"
                assert read == len(expected_buffer), "unpack_from_with_len (stream)"

        iter_buffer = build_iter_buffer(expected_buffer)
        for result in obj.iter_unpack(iter_buffer):
            assert result == expected_result, "iter_unpack (buffer)"
        with BytesIO(iter_buffer) as stream:
            for result in obj.iter_unpack(stream):
                assert result == expected_result, "iter_unpack (stream)"


def test_padding_standard():
    for args in range(4):
        c = std.Padding if args == 0 else std.Padding(args)
        args = args if args >= 1 else 1
        data = [((), bytearray(b"\x00" * args), ())]
        run_test_with_data(c, data)


def test_int_like_standards():
    MAX_ARGS = 4
    class_groups: List[Tuple[Type, int, bool]] = [(std.SByte, 1, True), (std.Byte, 1, False), (std.Short, 2, True), (std.UShort, 2, False), (std.Long, 8, True), (std.ULong, 8, False), (std.Int, 4, True), (std.UInt, 4, False)]
    for c_group, int_bytes, int_signed in class_groups:
        for args in range(MAX_ARGS):
            c = c_group if args == 0 else c_group(args)
            offsets = [c_group.alignment]  # Default is aligned, our tests dont account for that rn
            args = args if args >= 1 else 1
            m = ((2 ** (8 * int_bytes - 1)) - 1) // args
            v = tuple([_ * m for _ in range(args)])
            b_parts = [_.to_bytes(int_bytes, byteorder="little", signed=int_signed) for _ in v]
            b = bytearray()
            for _ in b_parts:
                b.extend(_)
            data = [(v, b, v)]
            try:
                run_test_with_data(c, data, offsets)
            except Exception as e:
                print(e)
                raise


def test_float_like_standards():
    class_groups = [(std.Half, Struct("e")), (std.Float, Struct("f")), (std.Double, Struct("d"))]
    floats: List[float] = [1.234567890, 867.5309, 21023, 1.11, 2.22, 3.33, 4.44, 5.55, 6.66, 7.77, 8.88, 9.99]
    for c_group, conv in class_groups:
        for args in range(len(floats)):
            c = c_group if args == 0 else c_group(args)
            offsets = [c.alignment]
            args = args if args >= 1 else 1
            v = tuple([floats[_] for _ in range(args)])
            b_parts = [conv.pack(_) for _ in v]
            r = tuple([conv.unpack(_)[0] for _ in b_parts])
            b = bytearray()
            for _ in b_parts:
                b.extend(_)
            data = [(v, b, r)]
            run_test_with_data(c, data, offsets)


def test_multi_struct_init():
    MultiStruct(Int16, Int16)
    MultiStruct(Int16(), Int16)
    MultiStruct(Int16(), Int16())


def test_multi_struct_unpack():
    Short4 = MultiStruct(Int16(4))
    s4 = (1, 2, 3, 4)
    s4_p = struct.pack("4h", *s4)
    s4_u = Short4.unpack(s4_p)
    assert s4_u == s4

    Float3 = MultiStruct(Float, Float, Float)
    f3 = (-1.0, 0.0, 1.0)
    f3_p = struct.pack("3f", *f3)
    f3_u = Float3.unpack(f3_p)
    assert f3_u == f3

    nested = MultiStruct(Short4, Float3)
    n = (s4, f3)
    n_p = bytearray()
    n_p.extend(s4_p)
    n_p.extend(f3_p)
    n_u = nested.unpack(n_p)
    assert n_u == n


def test_multi_struct():
    nested_floats = MultiStruct(std.Double, std.Float, std.Half)

    _floats = [-1.23456789, -1.0, -0.123456789, 0.0, 0.123456789, 1.0, 1.23456789]
    float_data = [((v, v, v), struct.pack("dfe", v, v, v), struct.unpack("dfe", struct.pack("dfe", v, v, v))) for v in _floats]
    run_test_with_data(nested_floats, float_data, offsets=[8])  # Use alignment of highest value


def test_multi_struct_nested():
    nested_floats = MultiStruct(std.Double, std.Float, std.Half)
    deep_nested_floats = MultiStruct(nested_floats, nested_floats, nested_floats)

    _floats = [-1.23456789, -1.0, -0.123456789, 0.0, 0.123456789, 1.0, 1.23456789]
    float_data = [((v, v, v), struct.pack("dfe", v, v, v), struct.unpack("dfe", struct.pack("dfe", v, v, v))) for v in _floats]

    nested_float_data = [((v, v, v), bytearray(b * 3), (r, r, r)) for v, b, r in float_data]
    run_test_with_data(deep_nested_floats, nested_float_data, offsets=[4])  # cant use 1
