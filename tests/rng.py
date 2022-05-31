import random
import sys
from typing import Callable

from structlib.byteorder import ByteOrderLiteral
from structlib.definitions.floating import _Float


def generate_random_chunks(chunk_size: int, chunk_count: int, seed: int):
    r = random.Random(seed)
    for _ in range(chunk_count):
        yield r.randbytes(chunk_size)


def generate_ints(chunk_count: int, seed: int, int_bit_size: int, signed: bool, byteorder: ByteOrderLiteral):
    for _ in generate_random_chunks(int_bit_size // 8, chunk_count, seed):
        yield int.from_bytes(_, byteorder, signed=signed)


def generate_seeds(count: int, seed: int):
    """
    Generates seeds from a starting seed.

    Expected use is 'seeding' the test file, using the test file 'seed' to generate seeds for each individual test.
    This allows tests to be consistent, while allowing test data to be randomized.

    :param count:
    :param seed:
    :return:
    """
    SEED_SIZE = 32
    return generate_ints(count, seed, SEED_SIZE, True, sys.byteorder)


def generate_floats(chunk_count: int, seed: int, int_bit_size: int, byteorder: ByteOrderLiteral):
    for _ in generate_random_chunks(int_bit_size // 8, chunk_count, seed):
        yield _Float.INTERNAL_STRUCTS[(int_bit_size, byteorder)].unpack(_)[0]


def generate_bools(chunk_count: int, seed: int, conv: Callable[[bytes], bool] = None):
    def convert(b: bytes) -> bool:
        return b[0] != 0x00

    conv = convert if conv is None else conv
    for _ in generate_random_chunks(1, chunk_count, seed):
        yield conv(_)


UNIQUE_STRING_POOL = {
    *"The Quick Brown Fox Jumped Over The Lazy Dog".split(),
    *"What It's Like To Be A Teenage Clone A Rope Of Sand".split(),
    *"She's Got A Little Book Of Conspiracies Right In Her Hand".split(),
}
STRING_POOL = list(UNIQUE_STRING_POOL)


def generate_strings(chunk_count: int, seed: int, max_str_size: int):
    rand = random.Random(seed)
    pool = STRING_POOL  # Previously we converted the unique pool to a list here

    for _ in range(chunk_count):
        s_buf = rand.choice(pool)
        while len(s_buf) < max_str_size and rand.choice([True, False]):
            s_buf += " " + rand.choice(pool)
        yield s_buf
