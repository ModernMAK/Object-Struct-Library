import unittest

from struct_obj.core import MultiStruct
from struct_obj.standard import Int16, Float
import struct


class MyTestCase(unittest.TestCase):
    def test_init(self):
        MultiStruct(Int16, Int16)
        MultiStruct(Int16(), Int16)
        MultiStruct(Int16(), Int16())

    def test_unpack(self):
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


if __name__ == '__main__':
    unittest.main()
