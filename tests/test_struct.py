from structlib.definitions import integer
from structlib.definitions.structure import Struct, DataTypeStructDefABC


class NestedType(DataTypeStructDefABC):
    def __init__(self, *args):
        # super.__init__() # ???? Why does it need arguments?
        self.a, self.b, self.c = args

    a: integer.Int8
    b: integer.Int16
    c: integer.UInt8


class ContainerType(DataTypeStructDefABC):
    def __init__(self, *args):
        # super.__init__() # ???? Why does it need arguments?
        self.a, self.b, self.c, self.d = args

    a: integer.Int8
    b: integer.Int16
    c: integer.UInt8
    d: NestedType


def test_nested():
    CLS = NestedType
    # LAYOUT = struct_definition(CLS)
    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]
    for args in zip(*SAMPLE_DATA):
        cls = CLS(*args)
        packed = cls.pack()
        # Int8 (Pad-Pre-Align Int16) Int16 Uint8 (Pad-Post-Align Struct)
        assert len(packed) == 1 + (1) + 2 + 1 + (1)  # (n) represents expected padding
        unpacked = CLS.unpack(packed)
        assert cls == unpacked


def test_container():
    CLS = ContainerType
    # LAYOUT = ContainerLayout
    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]

    for args in zip(*SAMPLE_DATA):
        inner = NestedType(*args)
        outer_args = [*args, inner]
        cls = CLS(*outer_args)
        packed = cls.pack()
        # TODO; this should be 12 [ (1 + (1) + 2 + 1 + (1)) * 2 ]
        #   But types currently don't pad themselves to their boundaries
        # Int8 (Pad-Pre-Align Int16) Int16 Uint8 (Pad-Post-Align Struct) [Nested is same as previous layout]
        assert len(packed) == (1 + (1) + 2 + 1 + (1)) * 2, packed  # (n) represents expceted padding
        unpacked = CLS.unpack(packed)
        assert cls == unpacked


def test_struct():
    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]
    my_data = Struct(
        integer.Int8,
        integer.Int16,
        integer.UInt8
    )
    for args in zip(*SAMPLE_DATA):
        packed = my_data.pack(*args)
        # Int8 (Pad-Pre-Align Int16) Int16 Uint8 (Pad-Post-Align Struct)
        assert len(packed) == 1 + (1) + 2 + 1 + (1)  # (n) represents expceted padding
        unpacked = my_data.unpack(packed)
        assert args == unpacked
