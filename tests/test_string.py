from typing import List

from shared import assert_pack_like, assert_buffer_pack_like, assert_stream_pack_like
from structlib.definitions.strings import StringBuffer, CStringBuffer
from structlib.protocols import calculate_padding, align_of, size_of

DEFAULT_OFFSETS = [0, 1, 2, 4, 8]  # Normal power sequence
DEFAULT_ALIGNS = [1, 2, 4, 8]  # 0 not acceptable alignment
DEFAULT_ORIGINS = [0, 1, 2, 4, 8]
DEFAULT_SAMPLES = 16  # Keep it low for faster; less comprehensive, tests

DEFAULT_SEED = 867 - 5309
TEST_SEEDS = {
    # For funsies, let's just try DEFAULT_SEED for
    # (8, True): 135,
    # (16, True): 123,
    # (32, True): 123,
    # (64, True): 123,
    # (16, True): 123,
}

SAMPLE_STRINGS = [
    "The",
    "Quick",
    "Brown",
    "Fox",
    "Jumped",
    "Over",
    "The",
    "Lazy",
    "Dog",
    "Apple",
    "Bananas",
    "Cherry",
    "Durian",
    "Eggplant",
    "Fig",
    "Grape",
    "Huckleberry",
    "Inca Berry",
    "Juniper Berry",
    "Kiwi",
    "Lemon",
    "Mango",
    "Orange",
    "Pomegranate",
]

# 
# def get_test_seed(size: int, signed: bool):
#     return TEST_SEEDS.get((size, signed), DEFAULT_SEED)


def test_string_buffer():
    generic_string_buffer_test(32, StringBuffer(32))


def generic_string_buffer_test(size, definition: StringBuffer = None, encoding: str = None):
    CLS = StringBuffer(size, encoding=encoding)
    if definition:  # Verify definition
        assert definition == CLS
    ENCODING = encoding if encoding is not None else "ascii"
    # DATA = list(range(0, (1 << 64), (1 << 56)))
    DATA = SAMPLE_STRINGS
    OFFSETS = DEFAULT_OFFSETS
    ORIGINS = DEFAULT_ORIGINS
    ALIGNS = DEFAULT_ALIGNS
    # Perform test with above args
    run_string_buffer_tests(CLS, ENCODING, DATA, OFFSETS, ORIGINS, ALIGNS)


def run_string_buffer_tests(cls: StringBuffer, encoding: str, sample_data: List[str], sample_offsets: List[int], sample_origins: List[int], sample_aligns: List[int]):
    size = size_of(cls)

    def str2buf(s: str) -> bytes:
        buf = bytearray(s.encode(encoding))
        if len(buf) < size:
            buf.extend([0x00] * (size - len(buf)))
        return buf

    def str2result(s:str) -> str:
        if len(s) < size:
            return s + "\0" * (size-len(s))

    def pack_like_tests():
        __ins = cls
        # Pack / Unpack
        for sample in sample_data:
            expected = str2result(sample)
            native_buffer = str2buf(sample)
            assert_pack_like(__ins, native_buffer, expected)

    def buffer_pack_like_tests_default():
        __ins = cls
        align = align_of(__ins)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def buffer_pack_like_tests(align: int):
        __ins = cls(align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    def stream_pack_like_tests_default():
        __ins = cls
        align = align_of(__ins)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    assert_stream_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def stream_pack_like_tests(align: int):
        __ins = cls(align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_stream_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # RUN ACTUAL TESTS
    pack_like_tests()
    buffer_pack_like_tests_default()
    for align in sample_aligns:
        buffer_pack_like_tests(align)
    stream_pack_like_tests_default()
    for align in sample_aligns:
        stream_pack_like_tests(align)


def test_cstring_buffer():
    generic_string_buffer_test(32, CStringBuffer(32))


def generic_cstring_buffer_test(size, definition: CStringBuffer = None, encoding: str = None):
    CLS = CStringBuffer(size, encoding=encoding)
    if definition:  # Verify definition
        assert definition == CLS
    ENCODING = encoding if encoding is not None else "ascii"
    DATA = SAMPLE_STRINGS
    OFFSETS = DEFAULT_OFFSETS
    ORIGINS = DEFAULT_ORIGINS
    ALIGNS = DEFAULT_ALIGNS
    # Perform test with above args
    run_string_buffer_tests(CLS, ENCODING, DATA, OFFSETS, ORIGINS, ALIGNS)


def run_cstring_buffer_tests(cls: StringBuffer, encoding: str, sample_data: List[str], sample_offsets: List[int], sample_origins: List[int], sample_aligns: List[int]):
    size = size_of(cls)

    def str2buf(s: str) -> bytes:
        buf = bytearray(s.encode(encoding))
        if len(buf) < size:
            buf.extend([0x00] * (size - len(buf)))
        return buf

    def str2result(s:str) -> str:
        return s.rstrip("\0")

    def pack_like_tests():
        __ins = cls
        # Pack / Unpack
        for sample in sample_data:
            expected = str2result(sample)
            native_buffer = str2buf(sample)
            assert_pack_like(__ins, native_buffer, expected)

    def buffer_pack_like_tests_default():
        __ins = cls
        align = align_of(__ins)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def buffer_pack_like_tests(align: int):
        __ins = cls(align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_buffer_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    def stream_pack_like_tests_default():
        __ins = cls
        align = align_of(__ins)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    assert_stream_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # CLS cant change alignment (or rather, it shouldn't)
    def stream_pack_like_tests(align: int):
        __ins = cls(align_as=align)
        # Pack Buffer / Unpack Buffer
        for sample in sample_data:
            native_buffer = str2buf(sample)
            expected = str2result(sample)

            for offset in sample_offsets:
                padding = calculate_padding(align, offset)
                for origin in sample_origins:
                    empty = bytearray([0x00] * (offset + origin + size + padding))

                    expected_native = empty[:]
                    expected_native[offset + origin + padding:offset + origin + size + padding] = native_buffer[:]

                    # Native Endian
                    assert_stream_pack_like(__ins, expected_native, expected, offset=offset, origin=origin)

    # RUN ACTUAL TESTS
    pack_like_tests()
    buffer_pack_like_tests_default()
    for align in sample_aligns:
        buffer_pack_like_tests(align)
    stream_pack_like_tests_default()
    for align in sample_aligns:
        stream_pack_like_tests(align)
