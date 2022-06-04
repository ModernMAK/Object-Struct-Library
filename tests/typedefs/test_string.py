from typing import List, Any

import rng
from typedefs.common_tests import  AlignmentTests, DefinitionTests, PrimitiveTests, Sample2Bytes
from typedefs.util import classproperty
from structlib.byteorder import ByteOrder
from structlib.protocols.packing import PrimitivePackable
from structlib.protocols.typedef import TypeDefAlignable
from structlib.typedefs.strings import StringBuffer, CStringBuffer


class TestString(PrimitiveTests, DefinitionTests,  AlignmentTests):
    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [StringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]

    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        return [StringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        return [
            StringBuffer(self.ARR_SIZE, encoding="utf-8"),
            StringBuffer(self.ARR_SIZE + 1, encoding=self.ENCODING),
        ]

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [StringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]

    @classproperty
    def BIG_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classproperty
    def LITTLE_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classproperty
    def NETWORK_PACKABLE(self) -> List[PrimitivePackable]:
        return []

    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder = None, alignment: int = None) -> Sample2Bytes:
        size = cls.ARR_SIZE
        ENCODING = cls.ENCODING

        def s2b(s: str) -> bytes:
            buf = bytearray(size)
            encoded = s.encode(ENCODING)
            buf[0:len(encoded)] = encoded
            return buf

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
    def SAMPLES(self) -> List[str]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        r = []
        arr_size = self.ARR_SIZE
        encoding = self.ENCODING
        for seed in seeds:
            for s in rng.generate_strings(s_per_seed, seed, arr_size):
                s_enc = s.encode(encoding)
                if len(s_enc) < arr_size:
                    s_enc = bytearray(s_enc)
                    s_enc.extend([0x00] * (arr_size - len(s_enc)))
                    s_dec = s_enc.decode(encoding)
                else:
                    s_dec = s
                r.append(s_dec)
        return r

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def ARR_SIZE(self) -> int:
        return 32

    @classproperty
    def NATIVE_SIZE(self) -> int:
        return self.ARR_SIZE

    @classproperty
    def ENCODING(self) -> str:
        return "ascii"

    @classproperty
    def DEFINITION(self) -> StringBuffer:
        return None  # String doesn't have a builtin def

    @classproperty
    def ALIGN(self) -> int:
        return 1


class TestCString(TestString):
    @classproperty
    def SAMPLES(self) -> List[str]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        r = []
        arr_size = self.ARR_SIZE
        for seed in seeds:
            gen = list(rng.generate_strings(s_per_seed, seed, arr_size))
            r.extend(gen)
        return r

    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [CStringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]

    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        return [CStringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        return [
            CStringBuffer(self.ARR_SIZE, encoding="utf-8"),
            CStringBuffer(self.ARR_SIZE + 1, encoding=self.ENCODING),
        ]

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [CStringBuffer(self.ARR_SIZE, encoding=self.ENCODING)]
