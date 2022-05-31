from typing import List, Literal

import rng
from definitions.common_tests.test_alignment import AlignmentTests
from definitions.common_tests.test_definition import DefinitionTests
from definitions.common_tests.test_endian import EndianTests, classproperty
from definitions.common_tests.test_primitive import PrimitiveTests, Sample2Bytes
from structlib.buffer_tools import calculate_padding
from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.definitions import integer as _integer, floating
from structlib.definitions.array import Array
from structlib.definitions.floating import _Float
from structlib.definitions.integer import IntegerDefinition
from structlib.packing.protocols import align_of, endian_of, native_size_of, endian_as


# AVOID using test as prefix
class ArrayTests(AlignmentTests, EndianTests, PrimitiveTests, DefinitionTests):
    """
    Represents a container for testing an Array
    """

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
            for gen_seeds in rng.generate_seeds(s_per_seed, seed):
                gen = self.INNER_SAMPLES(gen_seeds)
                r.append(gen)
        return r

    @classproperty
    def SEEDS(self) -> List[int]:
        # Random seed (unique per sub-test) and fixed seed
        return [hash(self.__name__), 5 * 23 * 2022]

    @classproperty
    def DEFINITION(self) -> Array:
        return None

    # Literal CONSTS; shouldn't change
    _LE: Literal["little"] = "little"
    _BE: Literal["big"] = "big"

    @classproperty
    def ARR_TYPE(self):
        raise NotImplementedError

    @classproperty
    def CLS(self) -> Array:
        return Array(self.ARR_SIZE, self.ARR_TYPE)

    @classproperty
    def CLS_LE(self) -> Array:
        return endian_as(self.CLS, self._LE)

    @classproperty
    def CLS_BE(self) -> Array:
        return endian_as(self.CLS, self._BE)

    @classproperty
    def INST(self) -> Array:
        return self.CLS()  # calling the instantiate method; not the property

    @classproperty
    def INST_LE(self) -> Array:
        return endian_as(self.INST, self._LE)

    @classproperty
    def INST_BE(self) -> Array:
        return endian_as(self.INST, self._BE)


class IntegerArrayTests(ArrayTests):
    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder, alignment: int) -> Sample2Bytes:
        internal_size = native_size_of(cls.ARR_TYPE)
        padded_size = calculate_padding(alignment,internal_size)
        byteorder = resolve_byteorder(endian)
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
        endian = endian_of(_type)
        gen = rng.generate_ints(cls.ARR_SIZE, seed, bit_size * 8, signed, endian)
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
        return _integer.Int8


class TestUInt8(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.UInt8


class TestInt16(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.Int16


class TestUInt16(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.UInt16


class TestInt32(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.Int32


class TestUInt32(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.UInt32


class TestInt64(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.Int64


class TestUInt64(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.UInt64


class TestInt128(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.Int128


class TestUInt128(IntegerArrayTests):
    @classproperty
    def ARR_TYPE(self) -> Array:
        return _integer.UInt128


class FloatArrayTests(ArrayTests):

    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder, alignment: int) -> Sample2Bytes:
        internal_size = native_size_of(cls.ARR_TYPE)
        padded_size = calculate_padding(alignment, internal_size)
        struct = _Float.INTERNAL_STRUCTS[(internal_size * 8, resolve_byteorder(endian))]
        padding = bytearray(padded_size)

        def wrapper(s: List[float]) -> bytes:
            converted = [struct.pack(_) for _ in s]
            full = padding.join(converted)
            # Append padding to last element
            full.extend(padding)
            return full

        return wrapper

    @classmethod
    def INNER_SAMPLES(cls, seed):
        _type: IntegerDefinition = cls.ARR_TYPE
        bit_size = native_size_of(_type)
        endian = endian_of(_type)
        gen = rng.generate_floats(cls.ARR_SIZE, seed, bit_size * 8, endian)
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
