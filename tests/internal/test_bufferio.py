from typing import Tuple

from structlib.io import bufferio


def create_sample_buffer(data: bytes, alignment: int = 1, offset: int = 0, origin: int = 0) -> Tuple[bytearray, int]:
    prefix_size = alignment - (offset % alignment) if offset % alignment != 0 else 0
    postfix_size = alignment - (len(data) % alignment) if len(data) % alignment != 0 else 0

    buffer_size = origin + offset + len(data) + prefix_size + postfix_size
    buffer = bytearray(b"\0" * buffer_size)
    start = origin + offset + prefix_size
    end = start + len(data)
    buffer[start:end] = data[:]
    wrote = buffer_size - origin - offset
    return buffer, wrote


def gen_sample_buffers(data: bytes) -> Tuple[Tuple[int, int, int], bytearray, int]:
    for alignment in [2, 4]:
        for offset in [0, 1]:
            for origin in [0, 1]:
                buffer, wrote = create_sample_buffer(data, alignment, offset, origin)
                yield (alignment, offset, origin), buffer, wrote


def test_write():
    data = b"Test!"
    for args, sample, sample_wrote in gen_sample_buffers(data):
        result_buffer = bytearray(b"\0" * len(sample))

        wrote = bufferio.write(result_buffer, data, *args)

        assert result_buffer == sample, (f"Alignment: {args[0]}, Offset: {args[1]}, Origin: {args[2]}")
        assert wrote == sample_wrote, (f"Alignment: {args[0]}, Offset: {args[1]}, Origin: {args[2]}")


def test_pad_data_to_boundary():
    data = b"Test!"
    for alignment in [2, 4]:
        expected_buffer, _ = create_sample_buffer(data, alignment)
        result_buffer = bufferio.pad_data_to_boundary(data, alignment)
        assert result_buffer, expected_buffer


def test_read():
    data = b"Test!"
    for args, sample, sample_wrote in gen_sample_buffers(data):
        read_size, read = bufferio.read(sample, len(data), *args)

        assert read == data, (f"Alignment: {args[0]}, Offset: {args[1]}, Origin: {args[2]}")
        assert read_size == sample_wrote, (f"Alignment: {args[0]}, Offset: {args[1]}, Origin: {args[2]}")


def test_create_padding_buffer():
    for pad_value in range(0, 256, 64):
        for pad_size in range(0, 16, 2):
            result = bufferio.create_padding_buffer(pad_size, pad_value)
            expected = bytes([pad_value] * pad_size)
            assert expected == result

