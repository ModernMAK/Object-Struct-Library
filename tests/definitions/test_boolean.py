from abc import ABC
from typing import List

import rng
from definitions.common_tests.test_alignment import AlignmentTests
from definitions.common_tests.test_definition import DefinitionTests
from definitions.common_tests.test_endian import EndianTests
from definitions.common_tests.test_primitive import PrimitiveTests, Sample2Bytes
from definitions.util import classproperty
from structlib.byteorder import ByteOrder
from structlib.definitions import boolean
from structlib.definitions.boolean import BooleanDefinition
from structlib.packing.protocols import endian_as


# AVOID using test as prefix
class BooleanTests(AlignmentTests, EndianTests, DefinitionTests, PrimitiveTests, ABC):
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
    def SAMPLES(self) -> List[bool]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        r = []
        for seed in seeds:
            gen = rng.generate_bools(s_per_seed, seed)
            r.extend(gen)
        return r

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 1

    @classproperty
    def ALIGN(self) -> int:
        return self.NATIVE_SIZE

    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder, alignment: int) -> Sample2Bytes:
        def s2b(b:bool) -> bytes:
            return bytes([0x01 if b else 0x00])
        return s2b

    @classproperty
    def CLS(self) -> BooleanDefinition:
        return BooleanDefinition(endian=self._NATIVE)

    @classproperty
    def CLS_LE(self) -> BooleanDefinition:
        return endian_as(self.CLS, self._LE)

    @classproperty
    def CLS_BE(self) -> BooleanDefinition:
        return endian_as(self.CLS, self._BE)

    @classproperty
    def INST(self) -> BooleanDefinition:
        return self.CLS()  # calling the instantiate method; not the property

    @classproperty
    def INST_LE(self) -> BooleanDefinition:
        return endian_as(self.INST, self._LE)

    @classproperty
    def INST_BE(self) -> BooleanDefinition:
        return endian_as(self.INST, self._BE)


class TestBoolean(BooleanTests):
    @classproperty
    def DEFINITION(self) -> BooleanDefinition:
        return boolean.Boolean
