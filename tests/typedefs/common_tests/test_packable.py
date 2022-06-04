import math
from io import BytesIO
from typing import List, Any, Callable

from typedefs.util import classproperty
from structlib.byteorder import ByteOrder, NativeEndian, NetworkEndian, LittleEndian, BigEndian
from structlib.protocols.packing import Packable
from structlib.protocols.typedef import align_as, calculate_padding


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


def NAN_CHECK(left, right) -> bool:
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) == len(right):  # check same size; if not, nan check doesn't matter
            def filter_nan(items):
                return [None if isinstance(item, float) and math.isnan(item) else item for item in items]

            ll, rr = filter_nan(left), filter_nan(right)
            return ll == rr

        return False
    else:
        return isinstance(left, float) and isinstance(right, float) and math.isnan(left) and math.isnan(right)


def sample2buffer(s: Any, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, alignment: int, offset: int, origin: int) -> bytes:
    prefix_align_padding = calculate_padding(alignment, offset)
    buffer = get_buffer(alignment, offset, origin)
    data = sample2bytes(s)
    # Copy data-portion of buffer to empty buffer
    start = origin + offset + prefix_align_padding
    buffer[start:start + len(data)] = data[:]
    return buffer


def assert_pack(t: Packable, sample2bytes: Sample2Bytes, samples: List[Any]):
    for sample in samples:
        buffer = sample2bytes(sample)
        packed = t.pack(sample)
        assert packed == buffer


def assert_unpack(t: Packable, sample2bytes: Sample2Bytes, samples: List[Any]):
    for sample in samples:
        buffer = sample2bytes(sample)
        unpacked = t.unpack(buffer)
        assert unpacked == sample or NAN_CHECK(sample, unpacked)


def assert_pack_equality(left: Packable, right: Packable, samples: List[Any]):
    for sample in samples:
        l_packed, r_packed = left.pack(sample), right.pack(sample)
        assert l_packed == r_packed


def assert_unpack_equality(left: Packable, right: Packable, sample2bytes: Sample2Bytes, samples: List[Any]):
    for sample in samples:
        buffer = sample2bytes(sample)
        l_unpacked, r_unpacked = left.unpack(buffer), right.unpack(buffer)
        assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


def assert_buffer_pack(t: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = get_buffer(alignment, offset, origin)
        expected = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        written = t.pack_buffer(buffer, sample, offset=offset, origin=origin)
        assert expected == buffer


def assert_buffer_unpack(t: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        read, unpacked = t.unpack_buffer(buffer, offset=offset, origin=origin)
        assert unpacked == sample or NAN_CHECK(sample, unpacked), f"Sample: `{sample}`, Align: `{alignment}`, Offset: `{offset}`, Origin: `{origin}`"


def assert_buffer_pack_equality(left: Packable, right: Packable, get_buffer: GetEmptyBuffer, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        l_empty, r_empty = get_buffer(alignment, offset, origin), get_buffer(alignment, offset, origin)
        l_written, r_written = left.pack_buffer(l_empty, sample, offset=offset, origin=origin), right.pack_buffer(r_empty, sample, offset=offset, origin=origin)
        assert l_empty == r_empty
        assert l_written == r_written


def assert_buffer_unpack_equality(left: Packable, right: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        (l_read, l_unpacked), (r_read, r_unpacked) = left.unpack_buffer(buffer, offset=offset, origin=origin), right.unpack_buffer(buffer, offset=offset, origin=origin)
        assert l_read == r_read
        assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


def assert_stream_pack(t: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        empty = get_buffer(alignment, offset, origin)
        expected = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(empty) as stream:
            stream.seek(origin + offset)
            written = t.pack_stream(stream, sample, origin=origin)
            stream.seek(0)
            buffer = stream.read()
            assert expected == buffer


def assert_stream_unpack(t: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(buffer) as stream:
            stream.seek(origin + offset)
            read, unpacked = t.unpack_stream(stream, origin=origin)
            assert unpacked == sample or NAN_CHECK(sample, unpacked)


def assert_stream_pack_equality(left: Packable, right: Packable, get_buffer: GetEmptyBuffer, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        l_empty, r_empty = get_buffer(alignment, offset, origin), get_buffer(alignment, offset, origin)
        with BytesIO(l_empty) as l_stream:
            with BytesIO(r_empty) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)
                l_written, r_written = left.pack_stream(l_stream, sample, origin=origin), right.pack_stream(r_stream, sample, origin=origin)

                l_stream.seek(0)
                r_stream.seek(0)

                l_packed, r_packed = l_stream.read(), r_stream.read()

                assert l_written == r_written
                assert l_packed == r_packed


def assert_stream_unpack_equality(left: Packable, right: Packable, get_buffer: GetEmptyBuffer, sample2bytes: Sample2Bytes, samples: List[Any], alignment: int, offset: int, origin: int):
    for sample in samples:
        buffer = sample2buffer(sample, get_buffer, sample2bytes, alignment, offset, origin)
        with BytesIO(buffer) as l_stream:
            with BytesIO(buffer) as r_stream:
                l_stream.seek(origin + offset)
                r_stream.seek(origin + offset)

                (l_read, l_unpacked), (r_read, r_unpacked) = left.unpack_stream(l_stream, origin=origin), right.unpack_stream(r_stream, origin=origin)

                assert l_read == r_read
                assert l_unpacked == r_unpacked or NAN_CHECK(l_unpacked, r_unpacked)


# AVOID using test as prefix
class PackableTests:

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
    def NATIVE_PACKABLE(self) -> List[Packable]:
        raise NotImplementedError

    @classproperty
    def BIG_PACKABLE(self) -> List[Packable]:
        raise NotImplementedError

    @classproperty
    def LITTLE_PACKABLE(self) -> List[Packable]:
        raise NotImplementedError

    @classproperty
    def NETWORK_PACKABLE(self) -> List[Packable]:
        raise NotImplementedError

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

    def get_all_sample2bytes(self, alignment):
        return self.get_sample2bytes(NativeEndian, alignment), \
               self.get_sample2bytes(BigEndian, alignment), \
               self.get_sample2bytes(LittleEndian, alignment), \
               self.get_sample2bytes(NetworkEndian, alignment)

    def get_all_typdef_groups(self):
        return [self.NATIVE_PACKABLE, self.BIG_PACKABLE, self.LITTLE_PACKABLE, self.NETWORK_PACKABLE]

    def test_pack(self):
        samples = self.SAMPLES
        s2bs = self.get_all_sample2bytes(self.ALIGN)
        typedef_groups = self.get_all_typdef_groups()

        for typedefs, s2b in zip(typedef_groups, s2bs):
            for typedef in typedefs:
                assert_pack(typedef, s2b, samples)

    def test_unpack(self):
        samples = self.SAMPLES
        s2bs = self.get_all_sample2bytes(self.ALIGN)
        typedef_groups = self.get_all_typdef_groups()

        for typedefs, s2b in zip(typedef_groups, s2bs):
            for typedef in typedefs:
                assert_unpack(typedef, s2b, samples)

    def test_pack_equality(self):
        samples = self.SAMPLES
        typedef_groups = self.get_all_typdef_groups()
        for typedefs in typedef_groups:
            for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                left, right = typedefs[i], typedefs[i + 1]
                assert_pack_equality(left, right, samples)

    def test_unpack_equality(self):
        samples = self.SAMPLES
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)
        for typedefs, s2b in zip(typedef_groups, s2bs):
            for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                left, right = typedefs[i], typedefs[i + 1]
                assert_unpack_equality(left, right, s2b, samples)

    def test_buffer_pack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for typedef in typedefs:
                        assert_buffer_pack(typedef, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        for typedef in typedefs:
                            aligned_typedef = align_as(typedef, align)
                            assert_buffer_pack(aligned_typedef, get_buf, s2b, samples, align, offset, origin)

    def test_buffer_unpack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for typedef in typedefs:
                        assert_buffer_unpack(typedef, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        for typedef in typedefs:
                            aligned_typedef = align_as(typedef, align)
                            assert_buffer_unpack(aligned_typedef, get_buf, s2b, samples, align, offset, origin)

    def test_buffer_pack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        # s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs in typedef_groups:
                    for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                        left, right = typedefs[i], typedefs[i + 1]
                        assert_buffer_pack_equality(left, right, get_buf, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    for typedefs in typedef_groups:
                        aligned_typedefs = align_as_many(*typedefs, align=align)
                        for i in range(len(aligned_typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                            left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
                            assert_buffer_pack_equality(left, right, get_buf, samples, align, offset, origin)

    def test_buffer_unpack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                        left, right = typedefs[i], typedefs[i + 1]
                        assert_buffer_unpack_equality(left, right, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        aligned_typedefs = align_as_many(*typedefs, align=align)
                        for i in range(len(aligned_typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                            left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
                            assert_buffer_unpack_equality(left, right, get_buf, s2b, samples, align, offset, origin)

    def test_stream_pack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for typedef in typedefs:
                        assert_stream_pack(typedef, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        for typedef in typedefs:
                            aligned_typedef = align_as(typedef, align)
                            assert_stream_pack(aligned_typedef, get_buf, s2b, samples, align, offset, origin)

    def test_stream_unpack(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for typedef in typedefs:
                        assert_stream_unpack(typedef, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        for typedef in typedefs:
                            aligned_typedef = align_as(typedef, align)
                            assert_stream_unpack(aligned_typedef, get_buf, s2b, samples, align, offset, origin)

    def test_stream_pack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        # s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs in typedef_groups:
                    for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                        left, right = typedefs[i], typedefs[i + 1]
                        assert_stream_pack_equality(left, right, get_buf, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    for typedefs in typedef_groups:
                        aligned_typedefs = align_as_many(*typedefs, align=align)
                        for i in range(len(aligned_typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                            left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
                            assert_stream_pack_equality(left, right, get_buf, samples, align, offset, origin)

    def test_stream_unpack_equality(self):
        samples = self.SAMPLES
        get_buf = self.get_empty_buffer_generator()
        typedef_groups = self.get_all_typdef_groups()
        s2bs = self.get_all_sample2bytes(self.ALIGN)

        for origin in self.ORIGINS:
            for offset in self.OFFSETS:
                for typedefs, s2b in zip(typedef_groups, s2bs):
                    for i in range(len(typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                        left, right = typedefs[i], typedefs[i + 1]
                        assert_stream_unpack_equality(left, right, get_buf, s2b, samples, self.ALIGN, offset, origin)

                for align in self.ALIGNMENTS:
                    aligned_s2bs = self.get_all_sample2bytes(align)
                    for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
                        aligned_typedefs = align_as_many(*typedefs, align=align)
                        for i in range(len(aligned_typedefs) - 1):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
                            left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
                            assert_stream_unpack_equality(left, right, get_buf, s2b, samples, align, offset, origin)
