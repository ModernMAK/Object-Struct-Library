import math
from io import BytesIO
from typing import List
from typing import Literal

import pytest

import rng
from definitions.test_alignment import AlignmentTests
from definitions.test_endian import EndianTests
from structlib.buffer_tools import calculate_padding
from structlib.definitions import integer as _integer, floating
from structlib.definitions.array import Array
from structlib.definitions.integer import IntegerDefinition
from structlib.packing.protocols import align_of, align_as, endian_of, native_size_of, endian_as, size_of
# Stolen from
# https://stackoverflow.com/qstions/128573/using-property-on-classmethods/64738850#64738850
# We don't use @classmethod + @property to allow <= 3.9 support
from structlib.packing.primitive import PrimitiveStructABC


class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


classproperty = ClassProperty  # Alias for decorator


def fix_nan(r: List) -> List:
    if isinstance(r[0], float):
        return [None if math.isnan(_) else _ for _ in r]
    else:
        return r


def sample2bytes(s: List, _type: PrimitiveStructABC) -> bytes:
    return _type.iter_pack(*s)


def align_as_many(*types, align: int):
    return tuple([align_as(t, align) for t in types])


def get_empty_buffer(native_size: int, alignment: int, offset: int, origin: int) -> bytearray:
    suffix_align_padding = calculate_padding(alignment, native_size)
    prefix_align_padding = calculate_padding(alignment, offset)
    # Origin + (Align to type boundary) + (Over aligned type buffer)
    buffer_size = origin + \
                  offset + prefix_align_padding + \
                  native_size + suffix_align_padding
    return bytearray(buffer_size)


def sample2buffer(s: List, _type: PrimitiveStructABC, alignment: int, offset: int, origin: int) -> bytes:
    size = size_of(_type) * len(s)
    buffer = get_empty_buffer(size, alignment, offset, origin)
    _type.iter_pack_buffer(buffer, *s, offset=offset, origin=origin)
    return buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_pack(t: Array, samples: List[List]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, t._backing)
        packed = t.pack(sample)
        assert buffer == packed


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_unpack(t: Array, samples: List[List]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, t._backing)
        unpacked = t.unpack(buffer)
        sample, unpacked = fix_nan(sample), fix_nan(unpacked)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_pack_equality(l: Array, r: Array, samples: List[List]):
    # Pack / Unpack
    for sample in samples:
        l_packed, r_packed = l.pack(sample), r.pack(sample)
        assert l_packed == r_packed


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_unpack_equality(l: Array, r: Array, samples: List[List]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, l._backing)
        l_unpacked, r_unpacked = l.unpack(buffer), r.unpack(buffer)
        l_unpacked, r_unpacked = fix_nan(l_unpacked), fix_nan(r_unpacked)
        assert l_unpacked == r_unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_pack(t: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    native = native_size_of(t)
    for sample in samples:
        buffer = get_empty_buffer(native, alignment, offset, origin)
        expected = sample2buffer(sample, t._backing, alignment, offset, origin)
        written = t.pack_buffer(buffer, sample, offset=offset, origin=origin)
        assert expected == buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_unpack(t: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, t._backing, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        sample, unpacked = fix_nan(sample), fix_nan(unpacked)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_pack_equality(l: Array, r: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    size = native_size_of(l)  # hack; array's native size is
    for sample in samples:
        l_buffer, r_buffer = get_empty_buffer(size, alignment, offset, origin), get_empty_buffer(size, alignment, offset, origin)
        l_written, r_written = l.pack_buffer(l_buffer, sample, offset=offset, origin=origin), r.pack_buffer(r_buffer, sample, offset=offset, origin=origin)
        assert l_buffer == r_buffer
        assert l_written == r_written


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_unpack_equality(l: Array, r: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, l._backing, alignment, offset, origin)
        (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_buffer(buffer, offset=offset, origin=origin), r.unpack_buffer(buffer, offset=offset, origin=origin)
        l_unpacked, r_unpacked = l.unpack(buffer), r.unpack(buffer)
        assert l_read == r_read
        l_unpacked, r_unpacked = fix_nan(l_unpacked), fix_nan(r_unpacked)
        assert l_unpacked == r_unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_pack(t: Array, samples: List[List], alignment: int, offset: int, origin: int):
    size = native_size_of(t)
    # Pack / Unpack
    for sample in samples:
        empty = get_empty_buffer(size, alignment, offset, origin)
        expected = sample2buffer(sample, t._backing, alignment, offset, origin)
        with BytesIO(empty) as stream:
            stream.seek(origin + offset)
            written = t.pack_stream(stream, sample, origin=origin)
            stream.seek(0)
            buffer = stream.read()
            assert expected == buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_unpack(t: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, t._backing, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        sample, unpacked = fix_nan(sample), fix_nan(unpacked)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_pack_equality(l: Array, r: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    size = size_of(l)
    for sample in samples:
        l_empty, r_empty = get_empty_buffer(size, alignment, offset, origin), get_empty_buffer(size, alignment, offset, origin)
        with BytesIO(l_empty) as l_stream:
            with BytesIO(r_empty) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)
                l_written, r_written = l.pack_stream(l_stream, sample, origin=origin), r.pack_stream(r_stream, sample, origin=origin)

                l_stream.seek(0)
                r_stream.seek(0)

                l_packed, r_packed = l_stream.read(), r_stream.read()

                assert l_written == r_written
                assert l_packed == r_packed


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_unpack_equality(l: Array, r: Array, samples: List[List], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, l._backing, alignment, offset, origin)
        with BytesIO(buffer) as l_stream:
            with BytesIO(buffer) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)

                (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_stream(l_stream, origin=origin), r.unpack_stream(r_stream, origin=origin)

                assert l_read == r_read
                l_unpacked, r_unpacked = fix_nan(l_unpacked), fix_nan(r_unpacked)
                assert l_unpacked == r_unpacked


# AVOID using test as prefix
class ArrayTests(AlignmentTests,EndianTests):
    """
    Represents a container for testing an Array

    Size / Signed `MUST BE` overridden in child classes
    """

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

    def test_definition_equality(self):
        _DEF = self.DEFINITION
        if _DEF is not None:
            assert self.CLS == _DEF
            assert self.INST == _DEF
        assert self.CLS == self.INST
        assert self.CLS_LE == self.INST_LE
        assert self.CLS_BE == self.INST_BE

    def test_definition_inequality(self):
        assert self.CLS_LE != self.CLS_BE
        assert self.CLS_LE != self.INST_BE
        assert self.INST_LE != self.CLS_BE
        assert self.INST_LE != self.INST_BE

    def test_pack(self):
        test_pack(self.CLS, self.SAMPLES)
        test_pack(self.INST, self.SAMPLES)

        test_pack(self.CLS_LE, self.SAMPLES)
        test_pack(self.INST_LE, self.SAMPLES)

        test_pack(self.CLS_BE, self.SAMPLES)
        test_pack(self.INST_BE, self.SAMPLES)

    def test_unpack(self):
        test_unpack(self.CLS, self.SAMPLES)
        test_unpack(self.INST, self.SAMPLES)

        test_unpack(self.CLS_LE, self.SAMPLES)
        test_unpack(self.INST_LE, self.SAMPLES)

        test_unpack(self.CLS_BE, self.SAMPLES)
        test_unpack(self.INST_BE, self.SAMPLES)

    def test_pack_equality(self):
        test_pack_equality(self.CLS, self.INST, self.SAMPLES)
        test_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES)
        test_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES)

    def test_unpack_equality(self):
        test_unpack_equality(self.CLS, self.INST, self.SAMPLES)
        test_unpack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES)
        test_unpack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES)

    def test_buffer_pack(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_pack(self.CLS, self.SAMPLES, align, offsets, origin)
                test_buffer_pack(self.INST, self.SAMPLES, align, offsets, origin)

                test_buffer_pack(self.CLS_LE, self.SAMPLES, align, offsets, origin)
                test_buffer_pack(self.INST_LE, self.SAMPLES, align, offsets, origin)

                test_buffer_pack(self.CLS_BE, self.SAMPLES, align, offsets, origin)
                test_buffer_pack(self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_pack(cls, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst, self.SAMPLES, align, offsets, origin)

                    test_buffer_pack(cls_le, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst_le, self.SAMPLES, align, offsets, origin)

                    test_buffer_pack(cls_be, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst_be, self.SAMPLES, align, offsets, origin)

    def test_buffer_unpack(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_unpack(self.CLS, self.SAMPLES, align, offsets, origin)
                test_buffer_unpack(self.INST, self.SAMPLES, align, offsets, origin)

                test_buffer_unpack(self.CLS_LE, self.SAMPLES, align, offsets, origin)
                test_buffer_unpack(self.INST_LE, self.SAMPLES, align, offsets, origin)

                test_buffer_unpack(self.CLS_BE, self.SAMPLES, align, offsets, origin)
                test_buffer_unpack(self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_unpack(cls, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst, self.SAMPLES, align, offsets, origin)

                    test_buffer_unpack(cls_le, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst_le, self.SAMPLES, align, offsets, origin)

                    test_buffer_unpack(cls_be, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst_be, self.SAMPLES, align, offsets, origin)

    def test_buffer_pack_equality(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_pack_equality(self.CLS, self.INST, self.SAMPLES, align, offsets, origin)
                test_buffer_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, align, offsets, origin)
                test_buffer_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_pack_equality(cls, inst, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack_equality(cls_le, inst_le, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack_equality(cls_be, inst_be, self.SAMPLES, align, offsets, origin)

    def test_buffer_unpack_equality(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_unpack_equality(self.CLS, self.INST, self.SAMPLES, align, offsets, origin)
                test_buffer_unpack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, align, offsets, origin)
                test_buffer_unpack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_unpack_equality(cls, inst, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack_equality(cls_le, inst_le, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack_equality(cls_be, inst_be, self.SAMPLES, align, offsets, origin)

    def test_stream_pack(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_pack(self.CLS, self.SAMPLES, align, offsets, origin)
                test_stream_pack(self.INST, self.SAMPLES, align, offsets, origin)

                test_stream_pack(self.CLS_LE, self.SAMPLES, align, offsets, origin)
                test_stream_pack(self.INST_LE, self.SAMPLES, align, offsets, origin)

                test_stream_pack(self.CLS_BE, self.SAMPLES, align, offsets, origin)
                test_stream_pack(self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_pack(cls, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst, self.SAMPLES, align, offsets, origin)

                    test_stream_pack(cls_le, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst_le, self.SAMPLES, align, offsets, origin)

                    test_stream_pack(cls_be, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst_be, self.SAMPLES, align, offsets, origin)

    def test_stream_unpack(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_unpack(self.CLS, self.SAMPLES, align, offsets, origin)
                test_stream_unpack(self.INST, self.SAMPLES, align, offsets, origin)

                test_stream_unpack(self.CLS_LE, self.SAMPLES, align, offsets, origin)
                test_stream_unpack(self.INST_LE, self.SAMPLES, align, offsets, origin)

                test_stream_unpack(self.CLS_BE, self.SAMPLES, align, offsets, origin)
                test_stream_unpack(self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_unpack(cls, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst, self.SAMPLES, align, offsets, origin)

                    test_stream_unpack(cls_le, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst_le, self.SAMPLES, align, offsets, origin)

                    test_stream_unpack(cls_be, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst_be, self.SAMPLES, align, offsets, origin)

    def test_stream_pack_equality(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_pack_equality(self.CLS, self.INST, self.SAMPLES, align, offsets, origin)
                test_stream_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, align, offsets, origin)
                test_stream_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_pack_equality(cls, inst, self.SAMPLES, align, offsets, origin)
                    test_stream_pack_equality(cls_le, inst_le, self.SAMPLES, align, offsets, origin)
                    test_stream_pack_equality(cls_be, inst_be, self.SAMPLES, align, offsets, origin)

    def test_stream_unpack_equality(self):
        align = align_of(self.CLS)
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_unpack_equality(self.CLS, self.INST, self.SAMPLES, align, offsets, origin)
                test_stream_unpack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, align, offsets, origin)
                test_stream_unpack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, align, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_unpack_equality(cls, inst, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack_equality(cls_le, inst_le, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack_equality(cls_be, inst_be, self.SAMPLES, align, offsets, origin)


class IntegerArrayTests(ArrayTests):
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
    def ARR_TYPE(self):
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
