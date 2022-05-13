import sys
from typing import List, Literal

from shared import assert_pack_equal, assert_unpack_equal, assert_pack_buffer_equal, assert_unpack_buffer_equal, assert_pack_like, assert_buffer_pack_like, assert_stream_pack_like, assert_pack_stream_equal, assert_unpack_stream_equal
from structlib.definitions import floating
from structlib.definitions.floating import _FloatHack as FloatDefinition, _FloatHack  # _FloatHack currently contains the code to convert floats to/from bytes which we will need even after FloatDefinition is properly implemented
from structlib.enums import Endian
from structlib.helper import ByteOrderLiteral
from structlib.utils import calculate_padding, align_of

DEFAULT_OFFSETS = [0, 1, 2, 4, 8]  # Normal power sequence
DEFAULT_ALIGNS = [1, 2, 4, 8]  # 0 not acceptable alignment
DEFAULT_ORIGINS = [0, 1, 2, 4, 8]
DEFAULT_SAMPLES = 16  # Keep it low for faster; less comprehensive, tests


def generate_subnormal_data(samples: int = DEFAULT_SAMPLES):
    for _ in range(samples):
        yield _ / samples


def generate_special_data():
    yield float("inf")
    yield float("-inf")
    yield float("nan")


def generate_data(min: float, max: float, samples: int = DEFAULT_SAMPLES):
    step = (max - min) / (samples - 1)
    for _ in range(samples):
        yield _ * step + min


def generate_all_data(min: float, max: float, samples: int = DEFAULT_SAMPLES):
    for _ in generate_data(min, max, samples):
        yield _
    for _ in generate_subnormal_data(samples):
        yield _
    for _ in generate_special_data():
        yield _


def test_float_16():
    default_float_test(16, floating.Float16)


def test_float_32():
    default_float_test(32, floating.Float32)


def test_float64():
    default_float_test(64, floating.Float64)


def default_float_test(size, definition: FloatDefinition = None):
    CLS = FloatDefinition(size)
    if definition:  # Verify definition
        assert definition == CLS
    SIZE = size
    BYTEORDER = sys.byteorder
    # DATA = list(range(0, (1 << 64), (1 << 56)))
    # This ensures our #s are representable in our precision
    # HACK: This is dangerous since we don't account for values not representable.
    DATA = list(from_bytes(to_bytes(_, SIZE, BYTEORDER), SIZE, BYTEORDER) for _ in generate_data(-12345.09876, 12345.09876))
    OFFSETS = DEFAULT_OFFSETS
    ORIGINS = DEFAULT_ORIGINS
    ALIGNS = DEFAULT_ALIGNS
    # Perform test with above args
    generic_float_test(CLS, SIZE, BYTEORDER, DATA, OFFSETS, ORIGINS, ALIGNS)


def to_bytes(f: float, s: int, b: ByteOrderLiteral) -> bytes:
    converter = _FloatHack.INTERNAL_STRUCTS[(s, b)]
    return converter.pack(f)


def from_bytes(buf: bytes, s: int, b: ByteOrderLiteral) -> float:
    converter = _FloatHack.INTERNAL_STRUCTS[(s, b)]
    return converter.unpack(buf)[0]


def generic_float_test(cls: FloatDefinition, size: int, byte_order: Literal["little", "big"], sample_data: List[float], sample_offsets: List[int], sample_origins: List[int], sample_aligns: List[int]):
    # _cls = cls
    # _ins = _cls()
    # _le = _cls(byteorder=Endian.Little)
    # _be = _cls(byteorder=Endian.Big)

    def pack_like_tests():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        # Pack / Unpack
        for sample in sample_data:
            native_buffer = to_bytes(sample, size, byte_order)
            le_buffer = to_bytes(sample, size, Endian.Little.value)
            be_buffer = to_bytes(sample, size, Endian.Big.value)

            # Native Endian
            assert_pack_like(__cls, native_buffer, sample, use_close=True)
            assert_pack_like(__ins, native_buffer, sample, use_close=True)

            # CLS == INST
            assert_pack_equal(__cls, __ins, sample, use_close=True)
            assert_unpack_equal(__cls, __ins, native_buffer, use_close=True)

            # Little Endian
            assert_pack_like(__le, le_buffer, sample, use_close=True)

            # Big Endian
            assert_pack_like(__be, be_buffer, sample, use_close=True)

    def buffer_pack_like_tests_default():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        align = align_of(__cls)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = to_bytes(sample, size, byte_order)
            le_buffer = to_bytes(sample, size, Endian.Little.value)
            be_buffer = to_bytes(sample, size, Endian.Big.value)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    expected_le = empty[:]
                    expected_le[offset + origin + padding:offset + origin + size + padding] = le_buffer[:]

                    expected_be = empty[:]
                    expected_be[offset + origin + padding:offset + origin + size + padding] = be_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__cls, expected_native, sample, offset=offset, origin=origin, use_close=True)
                    assert_buffer_pack_like(__ins, expected_native, sample, offset=offset, origin=origin, use_close=True)

                    # CLS == INST
                    assert_pack_buffer_equal(__cls, __ins, expected_native, sample, offset=offset, origin=origin, use_close=True)
                    assert_unpack_buffer_equal(__cls, __ins, expected_native, offset=offset, origin=origin, use_close=True)

                    # Little Endian
                    assert_buffer_pack_like(__le, expected_le, sample, offset=offset, origin=origin, use_close=True)

                    # Big Endian
                    assert_buffer_pack_like(__be, expected_be, sample, offset=offset, origin=origin, use_close=True)

    # CLS cant change alignment (or rather, it shouldn't)
    def buffer_pack_like_tests(align: int):
        __ins, __le, __be = cls(align_as=align), cls(byteorder=Endian.Little, align_as=align), cls(byteorder=Endian.Big, align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = to_bytes(sample, size, byte_order)
            le_buffer = to_bytes(sample, size, Endian.Little.value)
            be_buffer = to_bytes(sample, size, Endian.Big.value)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    expected_le = empty[:]
                    expected_le[offset + origin + padding:offset + origin + size + padding] = le_buffer[:]

                    expected_be = empty[:]
                    expected_be[offset + origin + padding:offset + origin + size + padding] = be_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__ins, expected_native, sample, offset=offset, origin=origin, use_close=True)

                    # Little Endian
                    assert_buffer_pack_like(__le, expected_le, sample, offset=offset, origin=origin, use_close=True)

                    # Big Endian
                    assert_buffer_pack_like(__be, expected_be, sample, offset=offset, origin=origin, use_close=True)

    def stream_pack_like_tests_default():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        align = align_of(__cls)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = to_bytes(sample, size, byte_order)
            le_buffer = to_bytes(sample, size, Endian.Little.value)
            be_buffer = to_bytes(sample, size, Endian.Big.value)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    expected_le = empty[:]
                    expected_le[offset + origin + padding:offset + origin + size + padding] = le_buffer[:]

                    expected_be = empty[:]
                    expected_be[offset + origin + padding:offset + origin + size + padding] = be_buffer[:]

                    # Native Endian
                    assert_stream_pack_like(__cls, expected_native, sample, offset=offset, origin=origin, use_close=True)
                    assert_stream_pack_like(__ins, expected_native, sample, offset=offset, origin=origin, use_close=True)

                    # CLS == INST
                    assert_pack_stream_equal(__cls, __ins, expected_native, sample, offset=offset, origin=origin, use_close=True)
                    assert_unpack_stream_equal(__cls, __ins, expected_native, offset=offset, origin=origin, use_close=True)

                    # Little Endian
                    assert_stream_pack_like(__le, expected_le, sample, offset=offset, origin=origin, use_close=True)

                    # Big Endian
                    assert_stream_pack_like(__be, expected_be, sample, offset=offset, origin=origin, use_close=True)

    # CLS cant change alignment (or rather, it shouldn't)
    def stream_pack_like_tests(align: int):
        __ins, __le, __be = cls(align_as=align), cls(byteorder=Endian.Little, align_as=align), cls(byteorder=Endian.Big, align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = to_bytes(sample, size, byte_order)
            le_buffer = to_bytes(sample, size, Endian.Little.value)
            be_buffer = to_bytes(sample, size, Endian.Big.value)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    expected_le = empty[:]
                    expected_le[offset + origin + padding:offset + origin + size + padding] = le_buffer[:]

                    expected_be = empty[:]
                    expected_be[offset + origin + padding:offset + origin + size + padding] = be_buffer[:]

                    # Native Endian
                    assert_stream_pack_like(__ins, expected_native, sample, offset=offset, origin=origin, use_close=True)

                    # Little Endian
                    assert_stream_pack_like(__le, expected_le, sample, offset=offset, origin=origin, use_close=True)

                    # Big Endian
                    assert_stream_pack_like(__be, expected_be, sample, offset=offset, origin=origin, use_close=True)

    # RUN ACTUAL TESTS
    pack_like_tests()
    buffer_pack_like_tests_default()
    for align in sample_aligns:
        buffer_pack_like_tests(align)
    stream_pack_like_tests_default()
    for align in sample_aligns:
        stream_pack_like_tests(align)
