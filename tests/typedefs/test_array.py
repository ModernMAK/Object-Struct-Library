from abc import ABC
from typing import List, Literal, Any

import rng
from typedefs.common_tests.test_alignment import AlignmentTests
from typedefs.common_tests.test_definition import DefinitionTests
from typedefs.common_tests.test_byteorder import ByteorderTests, classproperty
from typedefs.common_tests.test_primitive import PrimitiveTests, Sample2Bytes
from structlib.byteorder import ByteOrder, resolve_byteorder, NativeEndian, BigEndian, LittleEndian, NetworkEndian
from structlib.protocols.packing import PrimitivePackable
from structlib.protocols.typedef import TypeDefAlignable, align_of, native_size_of, byteorder_of, TypeDefByteOrder, byteorder_as, calculate_padding
from structlib.typedefs import integer, floating
from structlib.typedefs.array import Array
from structlib.typedefs.floating import FloatDefinition
from structlib.typedefs.integer import IntegerDefinition


# AVOID using test as prefix
class ArrayTests(AlignmentTests, PrimitiveTests, DefinitionTests, ABC):
    """
    Represents a container for testing an Array
    """

    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        return [Array(self.ARR_SIZE + 1, self.ARR_TYPE)]

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

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
    def ALIGN(self) -> int:
        return align_of(self.ARR_TYPE)

    @classproperty
    def NATIVE_SIZE(self) -> int:
        return native_size_of(self.ARR_TYPE) * self.ARR_SIZE

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
    def ARR_SIZE(self) -> int:
        return 2  # While 1 could also work; 2 ensures that the array logic should work for N-ry types

    @classmethod
    def INNER_SAMPLES(cls, seed):
        raise NotImplementedError

    @classproperty
    def SAMPLES(self) -> List[List]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        r = []
        for seed in seeds:
            for gen_seed in rng.generate_seeds(s_per_seed, seed):
                gen = self.INNER_SAMPLES(gen_seed)
                r.append(gen)
        return r

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def DEFINITION(self) -> Array:
        return None

    @classproperty
    def ARR_TYPE(self):
        raise NotImplementedError


class IntegerArrayTests(ArrayTests, ByteorderTests):
    @classproperty
    def BYTEORDER_TYPEDEFS(self) -> List[TypeDefByteOrder]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, byteorder_as(self.ARR_TYPE, NativeEndian))]

    @classproperty
    def BIG_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, byteorder_as(self.ARR_TYPE, BigEndian))]

    @classproperty
    def LITTLE_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, byteorder_as(self.ARR_TYPE, LittleEndian))]

    @classproperty
    def NETWORK_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, byteorder_as(self.ARR_TYPE, NetworkEndian))]

    @classmethod
    def get_sample2bytes(cls, byteorder: ByteOrder, alignment: int) -> Sample2Bytes:
        internal_size = native_size_of(cls.ARR_TYPE)
        padded_size = calculate_padding(alignment, internal_size)
        byteorder = resolve_byteorder(byteorder)
        signed = cls.ARR_TYPE._signed
        padding = bytearray(padded_size)

        def wrapper(s: List[int]) -> bytes:
            converted = [int.to_bytes(_, internal_size, byteorder, signed=signed) for _ in s]
            full = padding.join(converted)
            # Append padding to last element
            full.extend(padding)
            return full

        return wrapper

    @classmethod
    def INNER_SAMPLES(cls, seed):
        _type: IntegerDefinition = cls.ARR_TYPE
        bit_size = native_size_of(_type)
        signed = _type._signed
        byteorder = byteorder_of(_type)
        gen = rng.generate_ints(cls.ARR_SIZE, seed, bit_size * 8, signed, byteorder)
        return list(gen)

    @classproperty
    def DEFINITION(self) -> Array:
        return Array(self.ARR_SIZE, self.ARR_TYPE)

    @classproperty
    def ARR_TYPE(self) -> IntegerDefinition:
        raise NotImplementedError


class TestInt8(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.Int8


class TestUInt8(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.UInt8


class TestInt16(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.Int16


class TestUInt16(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.UInt16


class TestInt32(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.Int32


class TestUInt32(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.UInt32


class TestInt64(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.Int64


class TestUInt64(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.UInt64


class TestInt128(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.Int128


class TestUInt128(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return integer.UInt128


class FloatArrayTests(ArrayTests, ByteorderTests):

    @classproperty
    def BYTEORDER_TYPEDEFS(self) -> List[TypeDefByteOrder]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

    @classproperty
    def NATIVE_PACKABLE(self) -> List[PrimitivePackable]:
        return [Array(self.ARR_SIZE, self.ARR_TYPE)]

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
    def get_sample2bytes(cls, byteorder: ByteOrder, alignment: int) -> Sample2Bytes:
        _type: FloatDefinition = cls.ARR_TYPE
        byte_size = native_size_of(_type)
        padded_size = calculate_padding(alignment, byte_size)
        struct = FloatDefinition.INTERNAL_STRUCTS[(byte_size * 8, resolve_byteorder(byteorder))]
        padding = bytearray(padded_size)

        def wrapper(s: List[float]) -> bytes:
            converted = [struct.pack(_) for _ in s]
            full = padding.join(converted)
            # Append padding to last element-
            full.extend(padding)
            return full

        return wrapper

    @classmethod
    def INNER_SAMPLES(cls, seed):
        _type: FloatDefinition = cls.ARR_TYPE
        byte_size = native_size_of(_type)
        # byteorder = byteorder_of(_type)
        gen = rng.generate_floats(cls.ARR_SIZE, seed, byte_size * 8, NativeEndian)
        return list(gen)

    @classproperty
    def DEFINITION(self) -> Array:
        return Array(self.ARR_SIZE, self.ARR_TYPE)

    @classproperty
    def ARR_TYPE(self):
        raise NotImplementedError


class TestFloat16(FloatArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return floating.Float16


class TestFloat32(FloatArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return floating.Float32


class TestFloat64(FloatArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return floating.Float64
