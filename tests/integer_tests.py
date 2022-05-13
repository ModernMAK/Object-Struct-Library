import math
import sys
from typing import List, Literal

from shared import assert_pack_equal, assert_unpack_equal, assert_pack_buffer_equal, assert_unpack_buffer_equal, assert_pack_like, assert_buffer_pack_like, assert_stream_pack_like, assert_pack_stream_equal, assert_unpack_stream_equal
from structlib.definitions import integer
from structlib.definitions.integer import IntegerDefinition
from structlib.enums import Endian
from structlib.utils import calculate_padding, align_of

DEFAULT_OFFSETS = [0, 1, 2, 4, 8]  # Normal power sequence
DEFAULT_ALIGNS = [1, 2, 4, 8]  # 0 not acceptable alignment
DEFAULT_ORIGINS = [0, 1, 2, 4, 8]
DEFAULT_SAMPLES = 16  # Keep it low for faster; less comprehensive, tests


def generate_data(size: int, signed: bool, samples: int = DEFAULT_SAMPLES):
    min_val = 0
    delta = max_val = (1 << (8 * size))
    if signed:
        max_val //= 2
        min_val = -max_val + 1

    step = int(math.floor(delta / (samples - 1)))
    step = 1 if step <= 0 else step
    return list(range(min_val, max_val, step))


def test_int8():
    default_integer_test(1, True, integer.Int8)


def test_int16():
    default_integer_test(2, True, integer.Int16)


def test_int32():
    default_integer_test(4, True, integer.Int32)


def test_int64():
    default_integer_test(8, True, integer.Int64)


def test_int128():
    default_integer_test(16, True, integer.Int128)


def test_uint8():
    default_integer_test(1, False, integer.UInt8)


def test_uint16():
    default_integer_test(2, False, integer.UInt16)


def test_uint32():
    default_integer_test(4, False, integer.UInt32)


def test_uint64():
    default_integer_test(8, False, integer.UInt64)


def test_uint128():
    default_integer_test(16, False, integer.UInt128)


def default_integer_test(size, signed, definition: IntegerDefinition = None):
    CLS = IntegerDefinition(size, signed)
    if definition:  # Verify definition
        assert definition == CLS
    SIZE = size
    SIGNED = signed
    BYTEORDER = sys.byteorder
    # DATA = list(range(0, (1 << 64), (1 << 56)))
    DATA = generate_data(SIZE, SIGNED)
    OFFSETS = DEFAULT_OFFSETS
    ORIGINS = DEFAULT_ORIGINS
    ALIGNS = DEFAULT_ALIGNS
    # Perform test with above args
    generic_integer_test(CLS, SIZE, SIGNED, BYTEORDER, DATA, OFFSETS, ORIGINS, ALIGNS)


def generic_integer_test(cls: IntegerDefinition, size: int, signed: bool, byte_order: Literal["little", "big"], sample_data: List[int], sample_offsets: List[int], sample_origins: List[int], sample_aligns: List[int]):
    # _cls = cls
    # _ins = _cls()
    # _le = _cls(byteorder=Endian.Little)
    # _be = _cls(byteorder=Endian.Big)

    def pack_like_tests():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        # Pack / Unpack
        for sample in sample_data:
            native_buffer = int.to_bytes(sample, size, byte_order, signed=signed)
            le_buffer = int.to_bytes(sample, size, Endian.Little.value, signed=signed)
            be_buffer = int.to_bytes(sample, size, Endian.Big.value, signed=signed)

            # Native Endian
            assert_pack_like(__cls, native_buffer, sample)
            assert_pack_like(__ins, native_buffer, sample)

            # CLS == INST
            assert_pack_equal(__cls, __ins, sample)
            assert_unpack_equal(__cls, __ins, native_buffer)

            # Little Endian
            assert_pack_like(__le, le_buffer, sample)

            # Big Endian
            assert_pack_like(__be, be_buffer, sample)

    def buffer_pack_like_tests_default():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        align = align_of(__cls)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = int.to_bytes(sample, size, byte_order, signed=signed)
            le_buffer = int.to_bytes(sample, size, Endian.Little.value, signed=signed)
            be_buffer = int.to_bytes(sample, size, Endian.Big.value, signed=signed)

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
                    assert_buffer_pack_like(__cls, expected_native, sample, offset=offset, origin=origin)
                    assert_buffer_pack_like(__ins, expected_native, sample, offset=offset, origin=origin)

                    # CLS == INST
                    assert_pack_buffer_equal(__cls, __ins, expected_native, sample, offset=offset, origin=origin)
                    assert_unpack_buffer_equal(__cls, __ins, expected_native, offset=offset, origin=origin)

                    # Little Endian
                    assert_buffer_pack_like(__le, expected_le, sample, offset=offset, origin=origin)

                    # Big Endian
                    assert_buffer_pack_like(__be, expected_be, sample, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def buffer_pack_like_tests(align: int):
        __ins, __le, __be = cls(align_as=align), cls(byteorder=Endian.Little, align_as=align), cls(byteorder=Endian.Big, align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = int.to_bytes(sample, size, byte_order, signed=signed)
            le_buffer = int.to_bytes(sample, size, Endian.Little.value, signed=signed)
            be_buffer = int.to_bytes(sample, size, Endian.Big.value, signed=signed)

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
                    assert_buffer_pack_like(__ins, expected_native, sample, offset=offset, origin=origin)

                    # Little Endian
                    assert_buffer_pack_like(__le, expected_le, sample, offset=offset, origin=origin)

                    # Big Endian
                    assert_buffer_pack_like(__be, expected_be, sample, offset=offset, origin=origin)

    def stream_pack_like_tests_default():
        __cls, __ins, __le, __be = cls, cls(), cls(byteorder=Endian.Little), cls(byteorder=Endian.Big)
        align = align_of(__cls)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = int.to_bytes(sample, size, byte_order, signed=signed)
            le_buffer = int.to_bytes(sample, size, Endian.Little.value, signed=signed)
            be_buffer = int.to_bytes(sample, size, Endian.Big.value, signed=signed)

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
                    assert_stream_pack_like(__cls, expected_native, sample, offset=offset, origin=origin)
                    assert_stream_pack_like(__ins, expected_native, sample, offset=offset, origin=origin)

                    # CLS == INST
                    assert_pack_stream_equal(__cls, __ins, expected_native, sample, offset=offset, origin=origin)
                    assert_unpack_stream_equal(__cls, __ins, expected_native, offset=offset, origin=origin)

                    # Little Endian
                    assert_stream_pack_like(__le, expected_le, sample, offset=offset, origin=origin)

                    # Big Endian
                    assert_stream_pack_like(__be, expected_be, sample, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def stream_pack_like_tests(align: int):
        __ins, __le, __be = cls(align_as=align), cls(byteorder=Endian.Little, align_as=align), cls(byteorder=Endian.Big, align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = int.to_bytes(sample, size, byte_order, signed=signed)
            le_buffer = int.to_bytes(sample, size, Endian.Little.value, signed=signed)
            be_buffer = int.to_bytes(sample, size, Endian.Big.value, signed=signed)

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
                    assert_stream_pack_like(__ins, expected_native, sample, offset=offset, origin=origin)

                    # Little Endian
                    assert_stream_pack_like(__le, expected_le, sample, offset=offset, origin=origin)

                    # Big Endian
                    assert_stream_pack_like(__be, expected_be, sample, offset=offset, origin=origin)

    # RUN ACTUAL TESTS
    pack_like_tests()
    buffer_pack_like_tests_default()
    for align in sample_aligns:
        buffer_pack_like_tests(align)
    stream_pack_like_tests_default()
    for align in sample_aligns:
        stream_pack_like_tests(align)
