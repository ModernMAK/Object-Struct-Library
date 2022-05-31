import math
import sys
from io import BytesIO
from typing import List, Any, Callable, Iterable
from typing import Literal

from structlib.buffer_tools import calculate_padding
from structlib.byteorder import ByteOrder
from structlib.packing.primitive import PrimitiveStructABC
from structlib.packing.protocols import align_as


# Stolen from
# https://stackoverflow.com/qstions/128573/using-property-on-classmethods/64738850#64738850
# We don't use @classmethod + @property to allow <= 3.9 support


class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


classproperty = ClassProperty  # Alias for decorator


def get_empty_buffer(native_size: int, alignment: int, offset: int, origin: int) -> bytearray:
    suffix_align_padding = calculate_padding(alignment, native_size)
    prefix_align_padding = calculate_padding(alignment, offset)
    # Origin + (Align to type boundary) + (Over aligned type buffer)
    buffer_size = origin + \
                  offset + prefix_align_padding + \
                  native_size + suffix_align_padding
    return bytearray(buffer_size)


def align_as_many(*types, align: int):
    return tuple([align_as(t, align) for t in types])


Sample2Bytes = Callable[[Any], bytes]
GetEmptyBuffer = Callable[[int, int, int], bytearray]
Sample2Buffer = Callable[[Any, int, int, int], bytes]


def NAN_CHECK(l, r) -> bool:
    if isinstance(l,(list,tuple)) and isinstance(r,(list,tuple)):
        if len(l) == len(r):  # check same size; if not, nan check doesn't matter
            def filter_nan(items):
                return [None if isinstance(item, float) and math.isnan(item) else item for item in items]

            ll, rr = filter_nan(l), filter_nan(r)
            return ll == rr

        return False
    else:
        return isinstance(l, float) and isinstance(r, float) and math.isnan(l) and math.isnan(r)


def sample2buffer(s: Any, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, alignment: int, offset: int, origin: int) -> bytes:
    prefix_align_padding = calculate_padding(alignment, offset)
    buffer = get_buffer(alignment, offset, origin)
    data = sample2bytes(s)
    # Copy data-portion of buffer to empty buffer
    start = origin + offset + prefix_align_padding
    buffer[start:start + len(data)] = data[:]
    return buffer


def assert_pack(t: PrimitiveStructABC, sample2bytes: Sample2Bytes, samples: List[Any]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample)
        packed = t.pack(sample)
        assert buffer == packed


def assert_unpack(t: PrimitiveStructABC, sample2bytes: Sample2Bytes, samples: List[Any]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample)
        unpacked = t.unpack(buffer)
        assert sample == unpacked or NAN_CHECK(sample, unpacked)


def assert_pack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, samples: List[Any]):
    # Pack / Unpack
    for sample in samples:
        l_packed, r_packed = l.pack(sample), r.pack(sample)
        assert l_packed == r_packed


def assert_unpack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, sample2bytes: Sample2Bytes, samples: List[Any]):
    # Pack / Unpack
    for sample in samples:
        buffer = sample2bytes(sample)
        l_unpacked, r_unpacked = l.unpack(buffer), r.unpack(buffer)
        assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


def assert_buffer_pack(t: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    # Pack / Unpack
    for sample in samples:
        buffer = get_buffer(alignment, offset, origin)
        expected = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        written = t.pack_buffer(buffer, sample, offset=offset, origin=origin)
        assert expected == buffer


def assert_buffer_unpack(t: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        assert sample == unpacked or NAN_CHECK(sample, unpacked)


def assert_buffer_pack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, get_buffer: GetEmptyBuffer, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        l_empty, r_empty = get_buffer(alignment, offset, origin), get_buffer(alignment, offset, origin)
        l_written, r_written = l.pack_buffer(l_empty, sample, offset=offset, origin=origin), r.pack_buffer(r_empty, sample, offset=offset, origin=origin)
        assert l_empty == r_empty
        assert l_written == r_written


def assert_buffer_unpack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_buffer(buffer, offset=offset, origin=origin), r.unpack_buffer(buffer, offset=offset, origin=origin)
        assert l_read == r_read
        assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


def assert_stream_pack(t: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        empty = get_buffer(alignment, offset, origin)
        expected = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(empty) as stream:
            stream.seek(origin + offset)
            written = t.pack_stream(stream, sample, origin=origin)
            stream.seek(0)
            buffer = stream.read()
            assert expected == buffer


def assert_stream_unpack(t: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(buffer) as stream:
            stream.seek(origin + offset)
            read, unpacked = t.unpack_stream(stream, origin=origin)
            assert sample == unpacked or NAN_CHECK(sample, unpacked)


def assert_stream_pack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, get_buffer: GetEmptyBuffer, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        l_empty, r_empty = get_buffer(alignment, offset, origin), get_buffer(alignment, offset, origin)
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


def assert_stream_unpack_equality(l: PrimitiveStructABC, r: PrimitiveStructABC, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(buffer) as l_stream:
            with BytesIO(buffer) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)

                (l_read, l_unpacked), (r_read, r_unpacked) = l.unpack_stream(l_stream, origin=origin), r.unpack_stream(r_stream, origin=origin)

                assert l_read == r_read
                assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


# AVOID using test as prefix
class PrimitiveTests:

    @classproperty
    def OFFSETS(self) -> List[int]:
        raise NotImplementedError

    @classproperty
    def ALIGNMENTS(self) -> List[int]:
        raise NotImplementedError

    @classproperty
    def ORIGINS(self) -> List[int]:
        raise NotImplementedError

    @classproperty
    def SAMPLES(self) -> List[int]:
        raise NotImplementedError

    @classproperty
    def NATIVE_SIZE(self) -> int:
        raise NotImplementedError

    @classproperty
    def ALIGN(self) -> int:
        raise NotImplementedError

    @classproperty
    def CLS(self) -> Any:
        raise NotImplementedError

    @classproperty
    def CLS_LE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def CLS_BE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST_LE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST_BE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def ENDIAN_NATIVE_DEFS(self):
        yield self.CLS
        yield self.INST

    @classproperty
    def ENDIAN_LITTLE_DEFS(self):
        yield self.CLS_LE
        yield self.INST_LE

    @classproperty
    def ENDIAN_BIG_DEFS(self):
        yield self.CLS_BE
        yield self.INST_BE

    _NATIVE = sys.byteorder
    _LE: Literal["little"] = "little"
    _BE: Literal["big"] = "big"

    @classmethod
    def get_sample2bytes(cls, endian: ByteOrder, alignment: int) -> Sample2Bytes:
        """"""
        raise NotImplementedError

    @classmethod
    def get_empty_buffer_generator(cls) -> GetEmptyBuffer:
        size = cls.NATIVE_SIZE

        def wrapper(align, offset, origin):
            return get_empty_buffer(size, align, offset, origin)

        return wrapper

    def test_pack(self):
        samples = self.SAMPLES
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        for native in self.ENDIAN_NATIVE_DEFS:
            assert_pack(native, native_s2b, samples)

        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        for le in self.ENDIAN_LITTLE_DEFS:
            assert_pack(le, le_s2b, samples)

        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)
        for be in self.ENDIAN_BIG_DEFS:
            assert_pack(be, be_s2b, samples)

    def test_unpack(self):
        samples = self.SAMPLES
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        for native in self.ENDIAN_NATIVE_DEFS:
            assert_unpack(native, native_s2b, samples)

        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        for le in self.ENDIAN_LITTLE_DEFS:
            assert_unpack(le, le_s2b, samples)

        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)
        for be in self.ENDIAN_BIG_DEFS:
            assert_unpack(be, be_s2b, samples)

    def test_pack_equality(self):
        samples = self.SAMPLES
        assert_pack_equality(self.CLS, self.INST, samples)
        assert_pack_equality(self.CLS_LE, self.INST_LE, samples)
        assert_pack_equality(self.CLS_BE, self.INST_BE, samples)

    def test_unpack_equality(self):
        samples = self.SAMPLES
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)
        assert_unpack_equality(self.CLS, self.INST, native_s2b, samples)
        assert_unpack_equality(self.CLS_BE, self.INST_BE, le_s2b, samples)
        assert_unpack_equality(self.CLS_LE, self.INST_LE, be_s2b, samples)

    def test_buffer_pack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for native in self.ENDIAN_NATIVE_DEFS:
                    assert_buffer_pack(native, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                for be in self.ENDIAN_BIG_DEFS:
                    assert_buffer_pack(be, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                for le in self.ENDIAN_LITTLE_DEFS:
                    assert_buffer_pack(le, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE,align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE,align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE,align)
                    natives = align_as_many(*self.ENDIAN_NATIVE_DEFS, align=align)
                    bes = align_as_many(*self.ENDIAN_BIG_DEFS, align=align)
                    les = align_as_many(*self.ENDIAN_LITTLE_DEFS, align=align)

                    for native in natives:
                        assert_buffer_pack(native, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    for be in bes:
                        assert_buffer_pack(be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    for le in les:
                        assert_buffer_pack(le, get_buf, le_aligned_s2b, samples, align, offset, origin)

    def test_buffer_unpack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for native in self.ENDIAN_NATIVE_DEFS:
                    assert_buffer_unpack(native, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                for be in self.ENDIAN_BIG_DEFS:
                    assert_buffer_pack(be, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                for le in self.ENDIAN_LITTLE_DEFS:
                    assert_buffer_pack(le, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE,align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE,align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE,align)
                    natives = align_as_many(*self.ENDIAN_NATIVE_DEFS, align=align)
                    bes = align_as_many(*self.ENDIAN_BIG_DEFS, align=align)
                    les = align_as_many(*self.ENDIAN_LITTLE_DEFS, align=align)

                    for native in natives:
                        assert_buffer_pack(native, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    for be in bes:
                        assert_buffer_pack(be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    for le in les:
                        assert_buffer_pack(le, get_buf, le_aligned_s2b, samples, align, offset, origin)

    def test_buffer_pack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                assert_buffer_pack_equality(self.CLS, self.INST, get_buf, samples, self.ALIGN, offset, origin)
                assert_buffer_pack_equality(self.CLS_BE, self.INST_BE, get_buf, samples, self.ALIGN, offset, origin)
                assert_buffer_pack_equality(self.CLS_LE, self.INST_LE, get_buf, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    cls, inst = align_as_many(self.CLS, self.INST, align=align)
                    cls_be, inst_be = align_as_many(self.CLS_BE, self.INST_BE, align=align)
                    cls_le, inst_le = align_as_many(self.CLS_LE, self.INST_LE, align=align)

                    assert_buffer_pack_equality(cls, inst, get_buf, samples, align, offset, origin)
                    assert_buffer_pack_equality(cls_be, inst_be, get_buf, samples, align, offset, origin)
                    assert_buffer_pack_equality(cls_le, inst_le, get_buf, samples, align, offset, origin)

    def test_buffer_unpack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                assert_buffer_unpack_equality(self.CLS, self.INST, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                assert_buffer_unpack_equality(self.CLS_BE, self.INST_BE, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                assert_buffer_unpack_equality(self.CLS_LE, self.INST_LE, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    cls, inst = align_as_many(self.CLS, self.INST, align=align)
                    cls_be, inst_be = align_as_many(self.CLS_BE, self.INST_BE, align=align)
                    cls_le, inst_le = align_as_many(self.CLS_LE, self.INST_LE, align=align)
                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE, align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE, align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE, align)

                    assert_buffer_unpack_equality(cls, inst, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    assert_buffer_unpack_equality(cls_be, inst_be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    assert_buffer_unpack_equality(cls_le, inst_le, get_buf, le_aligned_s2b, samples, align, offset, origin)

    def test_stream_pack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for native in self.ENDIAN_NATIVE_DEFS:
                    assert_stream_pack(native, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                for be in self.ENDIAN_BIG_DEFS:
                    assert_stream_pack(be, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                for le in self.ENDIAN_LITTLE_DEFS:
                    assert_stream_pack(le, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE,align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE,align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE,align)
                    natives = align_as_many(*self.ENDIAN_NATIVE_DEFS, align=align)
                    bes = align_as_many(*self.ENDIAN_BIG_DEFS, align=align)
                    les = align_as_many(*self.ENDIAN_LITTLE_DEFS, align=align)

                    for native in natives:
                        assert_stream_pack(native, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    for be in bes:
                        assert_stream_pack(be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    for le in les:
                        assert_stream_pack(le, get_buf, le_aligned_s2b, samples, align, offset, origin)

    def test_stream_unpack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for native in self.ENDIAN_NATIVE_DEFS:
                    assert_stream_unpack(native, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                for be in self.ENDIAN_BIG_DEFS:
                    assert_stream_pack(be, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                for le in self.ENDIAN_LITTLE_DEFS:
                    assert_stream_pack(le, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE,align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE,align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE,align)
                    natives = align_as_many(*self.ENDIAN_NATIVE_DEFS, align=align)
                    bes = align_as_many(*self.ENDIAN_BIG_DEFS, align=align)
                    les = align_as_many(*self.ENDIAN_LITTLE_DEFS, align=align)

                    for native in natives:
                        assert_stream_pack(native, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    for be in bes:
                        assert_stream_pack(be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    for le in les:
                        assert_stream_pack(le, get_buf, le_aligned_s2b, samples, align, offset, origin)

    def test_stream_pack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                assert_stream_pack_equality(self.CLS, self.INST, get_buf, samples, self.ALIGN, offset, origin)
                assert_stream_pack_equality(self.CLS_BE, self.INST_BE, get_buf, samples, self.ALIGN, offset, origin)
                assert_stream_pack_equality(self.CLS_LE, self.INST_LE, get_buf, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    cls, inst = align_as_many(self.CLS, self.INST, align=align)
                    cls_be, inst_be = align_as_many(self.CLS_BE, self.INST_BE, align=align)
                    cls_le, inst_le = align_as_many(self.CLS_LE, self.INST_LE, align=align)

                    assert_stream_pack_equality(cls, inst, get_buf, samples, align, offset, origin)
                    assert_stream_pack_equality(cls_be, inst_be, get_buf, samples, align, offset, origin)
                    assert_stream_pack_equality(cls_le, inst_le, get_buf, samples, align, offset, origin)

    def test_stream_unpack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        native_s2b = self.get_sample2bytes(self._NATIVE,self.ALIGN)
        le_s2b = self.get_sample2bytes(self._LE,self.ALIGN)
        be_s2b = self.get_sample2bytes(self._BE,self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                assert_stream_unpack_equality(self.CLS, self.INST, get_buf, native_s2b, samples, self.ALIGN, offset, origin)
                assert_stream_unpack_equality(self.CLS_BE, self.INST_BE, get_buf, be_s2b, samples, self.ALIGN, offset, origin)
                assert_stream_unpack_equality(self.CLS_LE, self.INST_LE, get_buf, le_s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    cls, inst = align_as_many(self.CLS, self.INST, align=align)
                    cls_be, inst_be = align_as_many(self.CLS_BE, self.INST_BE, align=align)
                    cls_le, inst_le = align_as_many(self.CLS_LE, self.INST_LE, align=align)

                    native_aligned_s2b = self.get_sample2bytes(self._NATIVE,align)
                    le_aligned_s2b = self.get_sample2bytes(self._LE,align)
                    be_aligned_s2b = self.get_sample2bytes(self._BE,align)

                    assert_stream_unpack_equality(cls, inst, get_buf, native_aligned_s2b, samples, align, offset, origin)
                    assert_stream_unpack_equality(cls_be, inst_be, get_buf, be_aligned_s2b, samples, align, offset, origin)
                    assert_stream_unpack_equality(cls_le, inst_le, get_buf, le_aligned_s2b, samples, align, offset, origin)
