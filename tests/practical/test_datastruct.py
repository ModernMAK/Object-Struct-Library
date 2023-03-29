from dataclasses import dataclass

from structlib.typedefs.datastruct import DataStruct
from structlib.typedefs.integer import Int8, Int16, UInt8
from typing import get_type_hints


class SampleDataStruct(DataStruct):
    a: Int8
    b: Int16
    c: UInt8


@dataclass
class SampleDataClass:
    a: int
    b: int
    c: int


def test_datastruct():
    _ = SampleDataStruct()
    print(get_type_hints(SampleDataStruct))
    print(get_type_hints(_))
    _2 = SampleDataClass(0, 1, 2)
    print(get_type_hints(SampleDataClass))
    print(get_type_hints(_2))


if __name__ == "__main__":
    test_datastruct()
