import struct
import unittest
from io import BytesIO
from struct import Struct
from typing import Iterable, Tuple, List, Type

from struct_obj import standard as std
from struct_obj.core import StructObj, MultiStruct
from struct_obj.standard import Int16, Float


class MyTestCase(unittest.TestCase):
    def test_std_struct_hybrids(self):
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
            self.assertEqual(i.format, c.format)
            self.assertEqual(i.args, c.args)
            self.assertEqual(i.fixed_size, c.fixed_size)
            # self.assertEqual(i.min_size, c.min_size)
            self.assertEqual(i.byte_flags, c.byte_flags)
            if code in ['p']:  # not supported
                continue
            d = DATA[code]
            if d is None:
                i_dp, c_dp = i.pack(), c.pack()
            else:
                i_dp, c_dp = i.pack(d), c.pack(d)
            self.assertEqual(i_dp, c_dp)
            i_du, c_du = i.unpack(i_dp), c.unpack(c_dp)
            self.assertEqual(i_du, c_du)
            if d is None:
                self.assertEqual(i_du, ())
                self.assertEqual(c_du, ())
            else:
                self.assertEqual(i_du[0], d)
                self.assertEqual(c_du[0], d)

            struct_i, struct_c = Struct(i.format), Struct(c.format)
            if d is None:
                struct_i_dp, struct_c_dp = struct_i.pack(), struct_c.pack()
            else:
                struct_i_dp, struct_c_dp = struct_i.pack(d), struct_c.pack(d)
            self.assertEqual(i_dp, struct_i_dp)
            self.assertEqual(c_dp, struct_c_dp)
            self.assertEqual(struct_i_dp, struct_c_dp)

            struct_i_du, struct_c_du = i.unpack(i_dp), c.unpack(c_dp)
            self.assertEqual(struct_i_du, struct_c_du)
            if d is None:
                self.assertEqual(struct_i_du, ())
                self.assertEqual(struct_c_du, ())
            else:
                self.assertEqual(struct_i_du[0], d)
                self.assertEqual(struct_c_du[0], d)

    def build_offset_buffer(self, expected: bytes, offset: int = 1) -> Tuple[bytes, bytes]:
        e, w = bytearray(b"\x00" * offset), bytearray(b"\x00" * offset)
        e.extend(expected)
        w.extend(b"\x00" * len(expected))
        return e, w

    def build_iter_buffer(self, expected: bytes, repeat: int = 2) -> bytes:
        w = bytearray()
        for _ in range(repeat):
            w.extend(expected)
        return w

    def do_tests(self, obj: StructObj, data: Iterable[Tuple[Tuple, bytes, Tuple]]):
        OFFSETS = [1]
        for test_args, expected_buffer, expected_result in data:
            # PACK
            buffer = obj.pack(*test_args)
            self.assertEqual(buffer, expected_buffer)

            for offset in OFFSETS:
                # TEST BUFFER
                expected, writable = self.build_offset_buffer(expected_buffer, offset=offset)
                w = obj.pack_into(writable, *test_args, offset=offset)
                self.assertEqual(w, len(expected) - offset)
                self.assertEqual(expected, writable)

                # TEST STREAM
                expected, writable = self.build_offset_buffer(expected_buffer, offset=offset)
                with BytesIO(writable) as wrt_stream:
                    w = obj.pack_into(wrt_stream, *test_args, offset=offset)
                    wrt_stream.seek(0)
                    writable = wrt_stream.read()
                    self.assertEqual(w, len(expected) - offset)
                    self.assertEqual(expected, writable)

            with BytesIO() as wrt_stream:
                w = obj.pack_stream(wrt_stream, *test_args)
                wrt_stream.seek(0)
                buffer = wrt_stream.read()
                self.assertEqual(w, len(buffer))
                self.assertEqual(buffer, expected_buffer)

            # Unpack BUFFER
            r = obj.unpack(expected_buffer)
            self.assertEqual(r, expected_result)
            read, r = obj.unpack_with_len(expected_buffer)
            self.assertEqual(read, len(expected_buffer))
            self.assertEqual(r, expected_result)
            # Unpack STREAM
            with BytesIO(expected_buffer) as str_buffer:
                r = obj.unpack(str_buffer)
                self.assertEqual(r, expected_result)
                str_buffer.seek(0)
                read, r = obj.unpack_with_len(str_buffer)
                self.assertEqual(read, len(expected_buffer))
                self.assertEqual(r, expected_result)

            for offset in OFFSETS:
                # TEST BUFFER
                expected, _ = self.build_offset_buffer(expected_buffer, offset=offset)
                r = obj.unpack_from(expected, offset=offset)
                self.assertEqual(r, expected_result)
                read, r = obj.unpack_from_with_len(expected, offset=offset)
                self.assertEqual(r, expected_result)
                self.assertEqual(read, len(expected_buffer))

                # TEST STREAM
                expected, _ = self.build_offset_buffer(expected_buffer, offset=offset)
                with BytesIO(expected) as wrt_stream:
                    r = obj.unpack_from(expected, offset=offset)
                    self.assertEqual(r, expected_result)
                    wrt_stream.seek(0)
                    read, r = obj.unpack_from_with_len(expected, offset=offset)
                    self.assertEqual(r, expected_result)
                    self.assertEqual(read, len(expected_buffer))

            iter_buffer = self.build_iter_buffer(expected_buffer)
            for result in obj.iter_unpack(iter_buffer):
                self.assertEqual(result, expected_result)
            with BytesIO(iter_buffer) as stream:
                for result in obj.iter_unpack(stream):
                    self.assertEqual(result, expected_result)

    def test_padding(self):
        for args in range(4):
            c = std.Padding if args == 0 else std.Padding(args)
            args = args if args >= 1 else 1
            data = [((), bytearray(b"\x00" * args), ())]
            self.do_tests(c, data)

    def test_int_likes(self):
        MAX_ARGS = 4
        class_groups: List[Tuple[Type, int, bool]] = [(std.SByte, 1, True), (std.Byte, 1, False), (std.Short, 2, True), (std.UShort, 2, False), (std.Long, 8, True), (std.ULong, 8, False), (std.Int, 4, True), (std.UInt, 4, False)]
        for c_group, int_bytes, int_signed in class_groups:
            for args in range(MAX_ARGS):
                c = c_group if args == 0 else c_group(args)
                args = args if args >= 1 else 1
                m = ((2 ** (8 * int_bytes - 1)) - 1) // args
                v = tuple([_ * m for _ in range(args)])
                b_parts = [_.to_bytes(int_bytes, byteorder="little", signed=int_signed) for _ in v]
                b = bytearray()
                for _ in b_parts:
                    b.extend(_)
                data = [(v, b, v)]
                self.do_tests(c, data)

    def test_float_likes(self):
        class_groups = [(std.Half, Struct("e")), (std.Float, Struct("f")), (std.Double, Struct("d"))]
        floats: List[float] = [1.234567890, 867.5309, 21023, 1.11, 2.22, 3.33, 4.44, 5.55, 6.66, 7.77, 8.88, 9.99]
        for c_group, conv in class_groups:
            for args in range(len(floats)):
                c = c_group if args == 0 else c_group(args)
                args = args if args >= 1 else 1
                v = tuple([floats[_] for _ in range(args)])
                b_parts = [conv.pack(_) for _ in v]
                r = tuple([conv.unpack(_)[0] for _ in b_parts])
                b = bytearray()
                for _ in b_parts:
                    b.extend(_)
                data = [(v, b, r)]
                self.do_tests(c, data)

    def test_create_nested(self):
        MultiStruct(Int16, Int16)
        MultiStruct(Int16(), Int16)
        MultiStruct(Int16(), Int16())

    def test_nested_unpack(self):
        Short4 = MultiStruct(Int16(4))
        s4 = (1, 2, 3, 4)
        s4_p = struct.pack("4h", *s4)
        s4_u = Short4.unpack(s4_p)
        self.assertEqual(s4_u, s4)

        Float3 = MultiStruct(Float, Float, Float)
        f3 = (-1.0, 0.0, 1.0)
        f3_p = struct.pack("3f", *f3)
        f3_u = Float3.unpack(f3_p)
        self.assertEqual(f3_u, f3)

        nested = MultiStruct(Short4, Float3)
        n = (s4, f3)
        n_p = bytearray()
        n_p.extend(s4_p)
        n_p.extend(f3_p)
        n_u = nested.unpack(n_p)
        self.assertEqual(n_u, n)

    def test_nested(self):
        nested_floats = MultiStruct(std.Double, std.Float, std.Half)
        nested_ints = MultiStruct(std.Long, std.ULong, std.Int, std.UInt, std.Short, std.UShort, std.SByte, std.Byte)
        nested_special = MultiStruct(std.Bytes, std.Padding, std.Char, std.Boolean)
        nested_misc = MultiStruct(std.SizeT, std.SSizeT, std.CPointer)

        _floats = [-1.23456789, -1.0, -0.123456789, 0.0, 0.123456789, 1.0, 1.23456789]
        float_data = [((v, v, v), struct.pack("=dfe", v, v, v), struct.unpack("=dfe", struct.pack("=dfe", v, v, v))) for v in _floats]
        self.do_tests(nested_floats, float_data)

    def test_deep_nested(self):
        nested_floats = MultiStruct(std.Double, std.Float, std.Half)
        deep_nested_floats = MultiStruct(nested_floats, nested_floats, nested_floats)

        _floats = [-1.23456789, -1.0, -0.123456789, 0.0, 0.123456789, 1.0, 1.23456789]
        float_data = [((v, v, v), struct.pack("=dfe", v, v, v), struct.unpack("=dfe", struct.pack("=dfe", v, v, v))) for v in _floats]

        nested_float_data = [((v,v,v),bytearray(b*3), (r,r,r)) for v, b, r in float_data]
        self.do_tests(deep_nested_floats, nested_float_data)


if __name__ == '__main__':
    unittest.main()
