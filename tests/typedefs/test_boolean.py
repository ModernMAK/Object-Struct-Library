import itertools

import pytest

from rng import generate_bools
from structlib.typedef import align_of
from structlib.typedefs.boolean import BooleanDefinition
from tests.typedefs.common_tests import (
    AlignmentTests, IOPackableTests, PackableTests, TypedefInequalityTests, TypedefEqualityTests, )

_ALIGNMENTS = [1, 2, 4, 8]
_SAMPLE_COUNT = 16
_SEED = 8675309
_ORIGINS = [0, 1, 2]
_OFFSETS = [0, 1, 2]
_TEST_TYPEDEF_ARGS = _ALIGNMENTS
_TEST_TYPEDEFS_EQUAL = {
    (
        BooleanDefinition(alignment=alignment),
        BooleanDefinition(alignment=alignment)
    )
    for alignment in _TEST_TYPEDEF_ARGS
}

_TEST_TYPEDEFS = list(pair[0] for pair in _TEST_TYPEDEFS_EQUAL)
_TEST_TYPEDEFS_UNEQUAL = list(itertools.permutations(_TEST_TYPEDEFS, 2))


def get_packer(t, use_io:bool):
    alignment = align_of(t)

    def pack(v: bool):
        bool_buf = BooleanDefinition.TRUE_BUF if v else BooleanDefinition.FALSE_BUF
        if use_io:
            return bool_buf
        else:
            return bool_buf + b"\0" * (alignment - 1)


    return pack


_PACKERS = {t: get_packer(t,False) for t in _TEST_TYPEDEFS}
_PACKERSIO = {t: get_packer(t,True) for t in _TEST_TYPEDEFS}
_SAMPLES = {
    t: list(
        generate_bools(_SAMPLE_COUNT, _SEED)
    )
    for t in _TEST_TYPEDEFS
}

_TEST_TYPEDEF_PACKABLE = []
_TEST_TYPEDEF_PACKABLEIO = []
for t in _TEST_TYPEDEFS:
    for sample in _SAMPLES[t]:
        arg = t, sample, _PACKERS[t](sample)
        argio = t, sample, _PACKERSIO[t](sample)
        _TEST_TYPEDEF_PACKABLE.append(arg)
        _TEST_TYPEDEF_PACKABLEIO.append(argio)


@pytest.mark.parametrize(
    "alignment", _ALIGNMENTS, ids=[f"@{align}" for align in _ALIGNMENTS]
)
@pytest.mark.parametrize(
    "alignable_typedef",
    _TEST_TYPEDEFS,
    ids=[str(x).replace("-", "_") for x in _TEST_TYPEDEFS],
)
class TestBooleanAlignment(AlignmentTests):
    ...  # Obligatory 'do nothing' statement


@pytest.mark.parametrize(
    ["typedef", "equal_typedef"],
    _TEST_TYPEDEFS_EQUAL,
    ids=[f"{t} == {u}" for (t, u) in _TEST_TYPEDEFS_EQUAL],
)
class TestBooleanEquality(TypedefEqualityTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "unequal_typedef"],
    _TEST_TYPEDEFS_UNEQUAL,
    ids=[f"{t} != {u}" for (t, u) in _TEST_TYPEDEFS_UNEQUAL],
)
class TestBooleanInequality(TypedefInequalityTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "sample", "buffer"],
    _TEST_TYPEDEF_PACKABLE,
    ids=[f"`{t}` `{s}`" for (t, s, _) in _TEST_TYPEDEF_PACKABLE],
)
class TestBooleanPackable(PackableTests):
    ...


@pytest.mark.parametrize(
    ["typedef", "sample", "buffer"],
    _TEST_TYPEDEF_PACKABLEIO,
    ids=[f"`{t}` `{s}`" for (t, s, _) in _TEST_TYPEDEF_PACKABLEIO],
)
@pytest.mark.parametrize("origin", _ORIGINS)
@pytest.mark.parametrize("offset", _OFFSETS)
@pytest.mark.parametrize("alignment", _ALIGNMENTS)
class TestBooleanIOPackable(IOPackableTests):
    ...
