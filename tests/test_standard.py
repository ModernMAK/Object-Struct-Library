import unittest
from io import BytesIO
from struct import Struct
import standard as std


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
            # "p": b"\x01\x00", # IDK how this works, so i dont cover it; sorry
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

    def do_padding_cls(self):
        cls = std.Padding
        cls_buffers = (_.to_bytes(1, byteorder="little") for _ in range(255))

        r = cls.pack()
        self.assertEqual(r, b"\x00")

        buf = bytearray("\xea")
        l = cls.pack_into(buf)
        self.assertEqual(l, 1)
        self.assertEqual(buf, "\x00")

        buf = bytearray("\xbe\xaf")
        l = cls.pack_into(buf,offset=1)
        self.assertEqual(l, 1)
        self.assertEqual(buf, "\xbe\x00")

        for buf in cls_buffers:
            r = cls.unpack(buf)
            self.assertEqual(r, ())

            l, r = cls.unpack_with_len(buf)
            self.assertEqual(l, 1)
            self.assertEqual(r, ())

            l, r = cls.unpack_from_with_len(buf)
            self.assertEqual(l, 1)
            self.assertEqual(r, ())

            l, r = cls.unpack_from_with_len(buf, offset=0)
            self.assertEqual(l, 1)
            self.assertEqual(r, ())

            r = cls.unpack_from(buf)
            self.assertEqual(r, ())

            r = cls.unpack_from(buf, offset=0)
            self.assertEqual(r, ())

        for buf in cls_buffers:
            with BytesIO(buf) as s:
                r = cls.unpack(s)
                self.assertEqual(r, ())
                s.seek(0)

                r = cls.unpack_with_len(s)
                self.assertEqual(r, ())
                s.seek(0)

                l, r = cls.unpack_from_with_len(s)
                self.assertEqual(l, 1)
                self.assertEqual(r, ())
                s.seek(0)

                l, r = cls.unpack_from_with_len(s, offset=0)
                self.assertEqual(l, 1)
                self.assertEqual(r, ())
                s.seek(0)

                r = cls.unpack_from(s)
                self.assertEqual(r, ())
                s.seek(0)

                r = cls.unpack_from(s, offset=0)
                self.assertEqual(r, ())
                s.seek(0)

                l, r = cls.unpack_stream_with_len(s)
                self.assertEqual(l, 1)
                self.assertEqual(r, ())
                s.seek(0)

                r = cls.unpack_stream(s)
                self.assertEqual(r, ())
                s.seek(0)


if __name__ == '__main__':
    unittest.main()
