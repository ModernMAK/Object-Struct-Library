import itertools

import pytest

from rng import generate_ints
from structlib.byteorder import (
    LittleEndian,
    BigEndian,
)
from structlib.typedef import size_of, byteorder_of
from structlib.typedefs.integer import IntegerDefinition
from tests.typedefs.common_tests import (
    AlignmentTests,
)
from typedefs.common_tests import (
    ByteorderTests,
    PackableTests,
    TypedefEqualityTests,
    TypedefInequalityTests,
    IOPackableTests,
)

_ALIGNMENTS = [1, 2, 4, 8]
_BYTEORDERS = [BigEndian, LittleEndian]
_SAMPLE_COUNT = 16
_SEED = 8675309
_ORIGINS = [0, 1, 2]
_OFFSETS = [0, 1, 2]
_TEST_TYPEDEF_ARGS = list(
    itertools.product([1, 2, 4, 8, 16], [True, False], _BYTEORDERS)
)
_TEST_TYPEDEFS_EQUAL = {
    (
        IntegerDefinition(size, signed, alignment=size, byteorder=byteorder),
        IntegerDefinition(size, signed, alignment=size, byteorder=byteorder),
    )
    for (size, signed, byteorder) in _TEST_TYPEDEF_ARGS
}

_TEST_TYPEDEFS = list(pair[0] for pair in _TEST_TYPEDEFS_EQUAL)
_TEST_TYPEDEFS_UNEQUAL = list(itertools.permutations(_TEST_TYPEDEFS, 2))


def get_packer(t):
    signed = t._signed
    size = size_of(t)
    bom = byteorder_of(t)

    def pack(v: int):
        return v.to_bytes(size, bom, signed=signed)

    return pack


_PACKERS = {t: get_packer(t) for t in _TEST_TYPEDEFS}
_SAMPLES = {
    t: list(
        generate_ints(_SAMPLE_COUNT, _SEED, size_of(t) * 8, t._signed, byteorder_of(t))
    )
    for t in _TEST_TYPEDEFS
}

_TEST_TYPEDEF_PACKABLE = []
for t in _TEST_TYPEDEFS:
    for sample in _SAMPLES[t]:
        arg = t, sample, _PACKERS[t](sample)
        _TEST_TYPEDEF_PACKABLE.append(arg)


@pytest.mark.parametrize(
    "alignment", _ALIGNMENTS, ids=[f"@{align}" for align in _ALIGNMENTS]
)
@pytest.mark.parametrize(
    "alignable_typedef",
    _TEST_TYPEDEFS,
    ids=[str(x).replace("-", "_") for x in _TEST_TYPEDEFS],
)
class TestIntAlignment(AlignmentTests):
    ...  # Obligatory 'do nothing' statement


@pytest.mark.parametrize(
    "byteorder", _BYTEORDERS, ids=[f"bom_{b[0]}e" for b in _BYTEORDERS]
)
@pytest.mark.parametrize(
    "byteorder_typedef",
    _TEST_TYPEDEFS,
    ids=[str(x).replace("-", "_") for x in _TEST_TYPEDEFS],
)
class TestIntByteorder(ByteorderTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "equal_typedef"],
    _TEST_TYPEDEFS_EQUAL,
    ids=[f"{t} == {u}" for (t, u) in _TEST_TYPEDEFS_EQUAL],
)
class TestIntEquality(TypedefEqualityTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "unequal_typedef"],
    _TEST_TYPEDEFS_UNEQUAL,
    ids=[f"{t} != {u}" for (t, u) in _TEST_TYPEDEFS_UNEQUAL],
)
class TestIntInequality(TypedefInequalityTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "sample", "buffer"],
    _TEST_TYPEDEF_PACKABLE,
    ids=[f"`{t}` `{s}`" for (t, s, _) in _TEST_TYPEDEF_PACKABLE],
)
class TestIntPackable(PackableTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "sample", "buffer"],
    _TEST_TYPEDEF_PACKABLE,
    ids=[f"`{t}` `{s}`" for (t, s, _) in _TEST_TYPEDEF_PACKABLE],
)
@pytest.mark.parametrize("origin", _ORIGINS)
@pytest.mark.parametrize("offset", _OFFSETS)
@pytest.mark.parametrize("alignment", _ALIGNMENTS)
class TestIntIOPackable(IOPackableTests):
    ...
