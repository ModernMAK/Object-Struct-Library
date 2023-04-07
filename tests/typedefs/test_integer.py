from typing import List, Any

from tests import rng
from tests.typedefs.common_tests import AlignmentTests, DefinitionTests, ByteorderTests, PrimitiveTests, Sample2Bytes
from tests.typedefs.util import classproperty
from structlib.byteorder import ByteOrder, resolve_byteorder, NetworkEndian, LittleEndian, NativeEndian, BigEndian
from structlib.packing import Packable
from structlib.typedef import TypeDefAlignable, TypeDefByteOrder
from structlib.typedefs import integer as _integer
from structlib.typedefs.integer import IntegerDefinition
from structlib.utils import default_if_none


# AVOID using test as prefix
class IntegerTests(AlignmentTests, ByteorderTests, PrimitiveTests, DefinitionTests):
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
    def NATIVE_PACKABLE(self) -> List[Packable]:
        return [
            IntegerDefinition(self.NATIVE_SIZE, self.SIGNED, byteorder=NativeEndian)
        ]

    @classproperty
    def BIG_PACKABLE(self) -> List[Packable]:
        return [
            IntegerDefinition(self.NATIVE_SIZE, self.SIGNED, byteorder=BigEndian)
        ]

    @classproperty
    def LITTLE_PACKABLE(self) -> List[Packable]:
        return [
            IntegerDefinition(self.NATIVE_SIZE, self.SIGNED, byteorder=LittleEndian)
        ]

    @classproperty
    def NETWORK_PACKABLE(self) -> List[Packable]:
        return [
            IntegerDefinition(self.NATIVE_SIZE, self.SIGNED, byteorder=NetworkEndian)
        ]

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [*self.NATIVE_PACKABLE, *self.BIG_PACKABLE, *self.LITTLE_PACKABLE, *self.NETWORK_PACKABLE]

    @classproperty
    def BYTEORDER_TYPEDEFS(self) -> List[TypeDefByteOrder]:
        return [*self.NATIVE_PACKABLE, *self.BIG_PACKABLE, *self.LITTLE_PACKABLE, *self.NETWORK_PACKABLE]

    @classmethod
    def get_sample2bytes(cls, byteorder: ByteOrder = None, alignment: int = None) -> Sample2Bytes:
        byteorder = default_if_none(byteorder, NativeEndian)
        # alignment doesnt do anything? why'd i include it?
        size = cls.NATIVE_SIZE
        byteorder = resolve_byteorder(byteorder)
        signed = cls.SIGNED

        def s2b(s: int) -> bytes:
            return int.to_bytes(s, size, byteorder, signed=signed)

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
        signed = self.SIGNED
        byte_size = self.NATIVE_SIZE
        byteorder = NativeEndian
        r = []
        for seed in seeds:
            gen = rng.generate_ints(s_per_seed, seed, byte_size * 8, signed, byteorder=byteorder)
            r.extend(gen)
        return r

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def NATIVE_SIZE(self) -> int:
        raise NotImplementedError

    @classproperty
    def SIGNED(self) -> bool:
        raise NotImplementedError

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        raise NotImplementedError

    @classproperty
    def ALIGN(self) -> int:
        return self.NATIVE_SIZE


class TestInt8(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 1

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int8


class TestUInt8(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 1

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt8


class TestInt16(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 2

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int16


class TestUInt16(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 2

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt16


class TestInt32(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 4

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int32


class TestUInt32(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 4

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt32


class TestInt64(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 8

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int64


class TestUInt64(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 8

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt64


class TestInt128(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 16

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int128


class TestUInt128(IntegerTests):
    @classproperty
    def NATIVE_SIZE(self) -> int:
        return 16

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt128
