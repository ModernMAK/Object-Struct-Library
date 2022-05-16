from dataclasses import dataclass
from structlib.definitions import integer
from structlib.definitions.structure import Struct, StructDataclass


@dataclass
class TestInt:
    a: int
    b: int
    c: int


TestIntDataStruct = StructDataclass(
    integer.Int8,
    integer.Int16,
    integer.UInt8,
    dclass=TestInt
)

def test_data_struct():

    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]
    for args in zip(*SAMPLE_DATA):
        cls = TestInt(*args)
        packed = TestIntDataStruct.pack(cls)
        assert len(packed) == 1 + (1) + 2 + 1  # (n) represents expceted padding
        unpacked = TestIntDataStruct.unpack(packed)
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
        assert len(packed) == 1 + (1) + 2 + 1  # (n) represents expceted padding
        unpacked = my_data.unpack(packed)
        assert args == unpacked
