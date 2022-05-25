import sys
from io import BytesIO
from typing import List
from typing import Literal

import pytest

import rng
from definitions.test_alignment import AlignmentTests
from definitions.test_endian import EndianTests
from structlib.buffer_tools import calculate_padding
from structlib.byteorder import ByteOrder, resolve_byteorder, ByteOrderLiteral
from structlib.definitions import integer as _integer
from structlib.definitions.integer import IntegerDefinition
from structlib.packing.protocols import align_as, endian_as


# Stolen from
# https://stackoverflow.com/qstions/128573/using-property-on-classmethods/64738850#64738850
# We don't use @classmethod + @property to allow <= 3.9 support
class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


classproperty = ClassProperty  # Alias for decorator


def sample2bytes(s: int, size: int, byteorder: ByteOrder, signed: bool) -> bytes:
    return int.to_bytes(s, size, resolve_byteorder(byteorder), signed=signed)


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


def sample2buffer(s: int, size: int, byteorder: ByteOrder, signed: bool, alignment: int, offset: int, origin: int) -> bytes:
    prefix_align_padding = calculate_padding(alignment, offset)
    buffer = get_empty_buffer(size, alignment, offset, origin)
    data = sample2bytes(s, size, byteorder, signed)
    # Copy data-portion of buffer to empty buffer
    buffer[origin + offset + prefix_align_padding:origin + offset + prefix_align_padding + len(data)] = data
    return buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_pack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, size, byteorder, signed)
        packed = t.pack(sample)
        assert buffer == packed


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_unpack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, size, byteorder, signed)
        unpacked = t.unpack(buffer)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_pack_equality(l: IntegerDefinition, r: IntegerDefinition, samples: List[int]):
    # Pack / Unpack
    for sample in samples:
        l_packed, r_packed = l.pack(sample), r.pack(sample)
        assert l_packed == r_packed


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_unpack_equality(l: IntegerDefinition, r: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample, size, byteorder, signed)
        l_unpacked, r_unpacked = l.unpack(buffer), r.unpack(buffer)
        assert l_unpacked == r_unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_pack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = get_empty_buffer(size, alignment, offset, origin)
        expected = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        written = t.pack_buffer(buffer, sample, offset=offset, origin=origin)
        assert expected == buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_unpack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_pack_equality(l: IntegerDefinition, r: IntegerDefinition, samples: List[int], size, alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        l_empty, r_empty = get_empty_buffer(size, alignment, offset, origin), get_empty_buffer(size, alignment, offset, origin)
        l_written, r_written = l.pack_buffer(l_empty, sample, offset=offset, origin=origin), r.pack_buffer(r_empty, sample, offset=offset, origin=origin)
        assert l_empty == r_empty
        assert l_written == r_written


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_buffer_unpack_equality(l: IntegerDefinition, r: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_buffer(buffer, offset=offset, origin=origin), r.unpack_buffer(buffer, offset=offset, origin=origin)
        assert l_read == r_read
        assert l_unpacked == r_unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_pack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        empty = get_empty_buffer(size, alignment, offset, origin)
        expected = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        with BytesIO(empty) as stream:
            stream.seek(origin + offset)
            written = t.pack_stream(stream, sample, origin=origin)
            stream.seek(0)
            buffer = stream.read()
            assert expected == buffer


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_unpack(t: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        assert sample == unpacked


@pytest.mark.skip(reason="Helper method; included to allow pytest to reformat assertions.")
def test_stream_pack_equality(l: IntegerDefinition, r: IntegerDefinition, samples: List[int], size, alignment: int, offset: int, origin: int):
    # Pack / Unpack
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
def test_stream_unpack_equality(l: IntegerDefinition, r: IntegerDefinition, size: int, byteorder: ByteOrderLiteral, signed: bool, samples: List[int], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2buffer(sample, size, byteorder, signed, alignment, offset, origin)
        with BytesIO(buffer) as l_stream:
            with BytesIO(buffer) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)

                (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_stream(l_stream, origin=origin), r.unpack_stream(r_stream, origin=origin)

                assert l_read == r_read
                assert l_unpacked == r_unpacked


# AVOID using test as prefix
class IntegerTests(AlignmentTests,EndianTests):
    """
    Represents a container for testing an IntegerDefinition

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
    def SAMPLES(self) -> List[int]:
        s_count = self.SAMPLE_COUNT
        seeds = self.SEEDS
        s_per_seed = s_count // len(seeds)
        signed = self.SIGNED
        byte_size = self.SIZE
        byteorder = self.BYTEORDER
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
    def SIZE(self) -> int:
        return None

    @classproperty
    def SIGNED(self) -> bool:
        return None

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return None

    # Literal CONSTS; shouldn't change
    _LE: Literal["little"] = "little"
    _BE: Literal["big"] = "big"

    @classproperty
    def BYTEORDER(self) -> ByteOrderLiteral:
        return sys.byteorder

    @classproperty
    def ALIGN(self) -> int:
        return self.SIZE

    @classproperty
    def CLS(self) -> IntegerDefinition:
        return IntegerDefinition(self.SIZE, self.SIGNED, byteorder=self.BYTEORDER)

    @classproperty
    def CLS_LE(self) -> IntegerDefinition:
        return endian_as(self.CLS, self._LE)

    @classproperty
    def CLS_BE(self) -> IntegerDefinition:
        return endian_as(self.CLS, self._BE)

    @classproperty
    def INST(self) -> IntegerDefinition:
        return self.CLS()  # calling the instantiate method; not the property

    @classproperty
    def INST_LE(self) -> IntegerDefinition:
        return endian_as(self.INST, self._LE)

    @classproperty
    def INST_BE(self) -> IntegerDefinition:
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
        test_pack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)
        test_pack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)

        test_pack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES)
        test_pack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES)

        test_pack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES)
        test_pack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES)

    def test_unpack(self):
        test_unpack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)
        test_unpack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)

        test_unpack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES)
        test_unpack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES)

        test_unpack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES)
        test_unpack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES)

    def test_pack_equality(self):
        test_pack_equality(self.CLS, self.INST, self.SAMPLES)
        test_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES)
        test_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES)

    def test_unpack_equality(self):
        test_unpack_equality(self.CLS, self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)
        test_unpack_equality(self.CLS_BE, self.INST_BE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)
        test_unpack_equality(self.CLS_LE, self.INST_LE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES)

    def test_buffer_pack(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_pack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_pack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_buffer_pack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_pack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_buffer_pack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_pack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_pack(cls, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_buffer_pack(cls_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_buffer_pack(cls_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_pack(inst_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)

    def test_buffer_unpack(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_unpack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_unpack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_buffer_unpack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_unpack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_buffer_unpack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_unpack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_unpack(cls, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_buffer_unpack(cls_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_buffer_unpack(cls_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack(inst_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)

    def test_buffer_pack_equality(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_pack_equality(self.CLS, self.INST, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)
                test_buffer_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)
                test_buffer_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_pack_equality(cls, inst, self.SAMPLES, self.SIZE, align, offsets, origin)
                    test_buffer_pack_equality(cls_le, inst_le, self.SAMPLES, self.SIZE, align, offsets, origin)
                    test_buffer_pack_equality(cls_be, inst_be, self.SAMPLES, self.SIZE, align, offsets, origin)

    def test_buffer_unpack_equality(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_buffer_unpack_equality(self.CLS, self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_unpack_equality(self.CLS_LE, self.INST_LE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_buffer_unpack_equality(self.CLS_BE, self.INST_BE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_buffer_unpack_equality(cls, inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack_equality(cls_le, inst_le, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_buffer_unpack_equality(cls_be, inst_be, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)


    def test_stream_pack(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_pack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_pack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_stream_pack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_pack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_stream_pack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_pack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_pack(cls, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_stream_pack(cls_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_stream_pack(cls_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_pack(inst_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)

    def test_stream_unpack(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_unpack(self.CLS, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_unpack(self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_stream_unpack(self.CLS_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_unpack(self.INST_LE, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                test_stream_unpack(self.CLS_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_unpack(self.INST_BE, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_unpack(cls, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_stream_unpack(cls_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst_le, self.SIZE, self._LE, self.SIGNED, self.SAMPLES, align, offsets, origin)

                    test_stream_unpack(cls_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack(inst_be, self.SIZE, self._BE, self.SIGNED, self.SAMPLES, align, offsets, origin)

    def test_stream_pack_equality(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_pack_equality(self.CLS, self.INST, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)
                test_stream_pack_equality(self.CLS_LE, self.INST_LE, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)
                test_stream_pack_equality(self.CLS_BE, self.INST_BE, self.SAMPLES, self.SIZE, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_pack_equality(cls, inst, self.SAMPLES, self.SIZE, align, offsets, origin)
                    test_stream_pack_equality(cls_le, inst_le, self.SAMPLES, self.SIZE, align, offsets, origin)
                    test_stream_pack_equality(cls_be, inst_be, self.SAMPLES, self.SIZE, align, offsets, origin)

    def test_stream_unpack_equality(self):
        for origin in self.ORIGINS:
            for offsets in self.OFFSETS:
                test_stream_unpack_equality(self.CLS, self.INST, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_unpack_equality(self.CLS_LE, self.INST_LE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)
                test_stream_unpack_equality(self.CLS_BE, self.INST_BE, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, self.ALIGN, offsets, origin)

                for align in self.ALIGNMENTS:
                    cls, cls_le, cls_be = align_as_many(self.CLS, self.CLS_LE, self.CLS_BE, align=align)
                    inst, inst_le, inst_be = align_as_many(self.INST, self.INST_LE, self.INST_BE, align=align)

                    test_stream_unpack_equality(cls, inst, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack_equality(cls_le, inst_le, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)
                    test_stream_unpack_equality(cls_be, inst_be, self.SIZE, self.BYTEORDER, self.SIGNED, self.SAMPLES, align, offsets, origin)


class TestInt8(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 1

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int8


class TestUInt8(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 1

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt8


class TestInt16(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 2

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int16


class TestUInt16(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 2

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt16


class TestInt32(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 4

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int32


class TestUInt32(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 4

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt32


class TestInt64(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 8

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int64


class TestUInt64(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 8

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt64


class TestInt128(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 16

    @classproperty
    def SIGNED(self) -> bool:
        return True

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.Int128


class TestUInt128(IntegerTests):
    @classproperty
    def SIZE(self) -> int:
        return 16

    @classproperty
    def SIGNED(self) -> bool:
        return False

    @classproperty
    def DEFINITION(self) -> IntegerDefinition:
        return _integer.UInt128
