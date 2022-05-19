from dataclasses import dataclass
from structlib.definitions import integer
from structlib.definitions.structure import Struct, StructDataclass


@dataclass
class NestedType:
    e: int
    f: int
    g: int


@dataclass
class ContainerType:
    a: int
    b: int
    c: int
    d: NestedType


NestedLayout = StructDataclass(
    integer.Int8,
    integer.Int16,
    integer.UInt8,

    dclass=NestedType
)

ContainerLayout = StructDataclass(
    integer.Int8,
    integer.Int16,
    integer.UInt8,
    NestedLayout,

    dclass=ContainerType
)


def test_nested():
    CLS = NestedType
    LAYOUT = NestedLayout
    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]
    for args in zip(*SAMPLE_DATA):
        cls = CLS(*args)
        packed = LAYOUT.pack(cls)
        # Int8 (Pad-Pre-Align Int16) Int16 Uint8 (Pad-Post-Align Struct)
        assert len(packed) == 1 + (1) + 2 + 1 + (1)  # (n) represents expected padding
        unpacked = LAYOUT.unpack(packed).values[0]
        assert cls == unpacked


def test_container():
    CLS = ContainerType
    LAYOUT = ContainerLayout
    SAMPLE_DATA = [
        list(range(-128, 127)),
        list(range(-((2 ^ 15) - 1), 2 ^ 15, 256)),
        list(range(0, 256)),
    ]

    for args in zip(*SAMPLE_DATA):
        inner = NestedType(*args)
        outer_args = [*args, inner]
        cls = CLS(*outer_args)
        packed = LAYOUT.pack(cls)
        # TODO; this should be 12 [ (1 + (1) + 2 + 1 + (1)) * 2 ]
        #   But types currently don't pad themselves to their boundaries
        # Int8 (Pad-Pre-Align Int16) Int16 Uint8 (Pad-Post-Align Struct) [Nested is same as previous layout]
        assert len(packed) == (1 + (1) + 2 + 1 + (1)) * 2, packed  # (n) represents expceted padding
        unpacked = LAYOUT.unpack(packed).values[0]
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
        unpacked = my_data.unpack(packed).values
        assert args == unpacked
