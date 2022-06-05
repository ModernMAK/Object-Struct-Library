from typing import List, Any

from structlib.byteorder import ByteOrder
from structlib.protocols.packing import PrimitivePackable
from structlib.protocols.typedef import TypeDefAlignable
from structlib.typedefs import boolean
from structlib.typedefs.boolean import BooleanDefinition
from tests import rng
from tests.typedefs.common_tests import AlignmentTests, DefinitionTests, PrimitiveTests, Sample2Bytes
from tests.typedefs.util import classproperty


# AVOID using test as prefix
class BooleanTests(AlignmentTests, DefinitionTests, PrimitiveTests):
    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        return [BooleanDefinition()]

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        return [BooleanDefinition(alignment=2)]

    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [BooleanDefinition()]

    @classproperty
    def BIG_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classproperty
    def LITTLE_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classproperty
    def NETWORK_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classproperty
    def OFFSETS(self) -> List[int]:
        return [0, 1, 2, 4, 8]  # Normal power sequence

    @classproperty
    def ALIGNMENTS(self) -> List[int]:
        return [1, 2, 4, 8]  # 0 not acceptable alignment

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [BooleanDefinition()]

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



class TestBoolean(BooleanTests):
    @classproperty
    def DEFINITION(self) -> BooleanDefinition:
        return boolean.Boolean
