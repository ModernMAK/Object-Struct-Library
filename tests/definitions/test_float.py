from typing import List

import rng
from definitions.common_tests.test_alignment import AlignmentTests
from definitions.common_tests.test_definition import DefinitionTests
from definitions.common_tests.test_endian import EndianTests
from definitions.common_tests.test_primitive import PrimitiveTests, Sample2Bytes
from definitions.util import classproperty
from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.definitions import floating as _float
from structlib.definitions.floating import _Float
from structlib.packing.protocols import endian_as


# AVOID using test as prefix
class FloatTests(AlignmentTests, EndianTests, DefinitionTests, PrimitiveTests):
    """
    Represents a container for testing an _Float
    """

    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder, alignment: int) -> Sample2Bytes:
        struct = _Float.INTERNAL_STRUCTS[(cls.NATIVE_SIZE * 8, resolve_byteorder(endian))]

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
        byteorder = self._NATIVE
        r = []
        for seed in seeds:
            gen = rng.generate_floats(s_per_seed, seed, byte_size * 8, byteorder=byteorder)
            r.extend(gen)
        return r

    @classproperty
    def ALIGN(self) -> int:
        return self.NATIVE_SIZE

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def CLS(self) -> _Float:
        return _Float(self.NATIVE_SIZE * 8, byteorder=self._NATIVE)

    @classproperty
    def CLS_LE(self) -> _Float:
        return endian_as(self.CLS, self._LE)

    @classproperty
    def CLS_BE(self) -> _Float:
        return endian_as(self.CLS, self._BE)

    @classproperty
    def INST(self) -> _Float:
        return self.CLS()  # calling the instantiate method; not the property

    @classproperty
    def INST_LE(self) -> _Float:
        return endian_as(self.INST, self._LE)

    @classproperty
    def INST_BE(self) -> _Float:
        return endian_as(self.INST, self._BE)


class TestFloat16(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 2

    @classproperty
    def DEFINITION(self) -> _Float:
        return _float.Float16


class TestFloat32(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 4

    @classproperty
    def DEFINITION(self) -> _Float:
        return _float.Float32


class TestFloat64(FloatTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 8

    @classproperty
    def DEFINITION(self) -> _Float:
        return _float.Float64
