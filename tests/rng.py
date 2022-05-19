import random

from structlib.byteorder import ByteOrderLiteral


def generate_random_chunks(chunk_size: int, chunk_count: int, seed: int):
    r = random.Random(seed)
    for _ in range(chunk_count):
        yield r.randbytes(chunk_size)


def generate_ints(chunk_count: int, seed: int, int_bit_size: int, signed: bool, byteorder: ByteOrderLiteral):
    for _ in generate_random_chunks(int_bit_size // 8, chunk_count, seed):
        yield int.from_bytes(_, byteorder, signed=signed)
