from typing import List, Any

import structlib.packing
from structlib.byteorder import (
    ByteOrder,
    resolve_byteorder,
    NativeEndian,
    BigEndian,
    LittleEndian,
    NetworkEndian,
)
from structlib.typedef import TypeDefAlignable, TypeDefByteOrder
from structlib.typedefs import floating as _float
from structlib.typedefs.floating import FloatDefinition
from tests import rng
from tests.typedefs.common_tests import (
    AlignmentTests,
    PrimitiveTests,
    Sample2Bytes,
)
from typedefs.common_tests import ByteorderTests, DefinitionTests
from tests.typedefs.util import classproperty


# AVOID using test as prefix
class FloatTests(AlignmentTests, ByteorderTests, DefinitionTests, PrimitiveTests):
    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        if NativeEndian == "big":
            return [*self.NATIVE_PACKABLE, *self.BIG_PACKABLE, *self.NETWORK_PACKABLE]
        else:
            return [*self.NATIVE_PACKABLE, *self.LITTLE_PACKABLE]

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        if NativeEndian == "little":
            return [*self.BIG_PACKABLE, *self.NETWORK_PACKABLE]
        else:
            return self.LITTLE_PACKABLE

    @classproperty
    def NATIVE_PACKABLE(self) -> list[FloatDefinition]:
        return [FloatDefinition(self.NATIVE_SIZE * 8, byteorder=NativeEndian)]

    @classproperty
    def BIG_PACKABLE(self) -> list[FloatDefinition]:
        return [FloatDefinition(self.NATIVE_SIZE * 8, byteorder=BigEndian)]

    @classproperty
    def LITTLE_PACKABLE(self) -> list[FloatDefinition]:
        return [FloatDefinition(self.NATIVE_SIZE * 8, byteorder=LittleEndian)]

    @classproperty
    def NETWORK_PACKABLE(self) -> list[FloatDefinition]:
        return [FloatDefinition(self.NATIVE_SIZE * 8, byteorder=NetworkEndian)]

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [
            *self.NATIVE_PACKABLE,
            *self.BIG_PACKABLE,
            *self.LITTLE_PACKABLE,
            *self.NETWORK_PACKABLE,
        ]

    @classproperty
    def BYTEORDER_TYPEDEFS(self) -> List[TypeDefByteOrder]:
        return [
            *self.NATIVE_PACKABLE,
            *self.BIG_PACKABLE,
            *self.LITTLE_PACKABLE,
            *self.NETWORK_PACKABLE,
        ]

    @classmethod
    def get_sample2bytes(cls, byteorder: ByteOrder, alignment: int) -> Sample2Bytes:
        struct = FloatDefinition.INTERNAL_STRUCTS[
            (cls.NATIVE_SIZE * 8, resolve_byteorder(byteorder))
        ]

        def s2b(s):
            return struct.pack(s)

        return s2b

    @classproperty
    def OFFSETS(self) -> List[int]:
        return [0, 1, 2, 4, 8]  # Normal power sequence

    @classproperty
    def ALIGNMENTS(self) -> List[int]:
        return [1, 2, 4, 8]  # 0 not acceptable alignment

    @classproperty
    def ORIGINS(self) -> List[int]:
        return [0, 1, 2, 4, 8]

    @classproperty
    def SAMPLE_COUNT(self) -> int:
        # Keep it low for faster; less comprehensive, tests
        return 16

    @classproperty
    def SAMPLES(self) -> List[int]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        byte_size = self.NATIVE_SIZE
        byteorder = NativeEndian
        r = []
        for seed in seeds:
            gen = rng.generate_floats(
                s_per_seed, seed, byte_size * 8, byteorder=byteorder
            )
            r.extend(gen)
        return r

    @classproperty
    def ALIGN(self) -> int:
        return self.NATIVE_SIZE

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]


class TestFloat16(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 2

    @classproperty
    def DEFINITION(self) -> FloatDefinition:
        return _float.Float16


class TestFloat32(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 4

    @classproperty
    def DEFINITION(self) -> FloatDefinition:
        return _float.Float32


class TestFloat64(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 8

    @classproperty
    def DEFINITION(self) -> FloatDefinition:
        return _float.Float64
