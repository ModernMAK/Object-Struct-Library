import warnings
from typing import List, Any

from structlib.packing.protocols import align_of, align_as


# Stolen from
# https://stackoverflow.com/qstions/128573/using-property-on-classmethods/64738850#64738850
# We don't use @classmethod + @property to allow <= 3.9 support
class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


classproperty = ClassProperty  # Alias for decorator


# AVOID using test as prefix
class AlignmentTests:
    """
    Represents a container for testing an BooleanDefinition
    """

    @classproperty
    def ALIGNMENTS(self) -> List[int]:
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

    def test_align_as(self):
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for align in self.ALIGNMENTS:
            for t in types:
                new_t = align_as(t, align)
                assert align_of(new_t) == align, "`align_of` not getting value set by `align_as`!"

    def test_align_as_preserves_type(self):
        # A new types should be returned by align_as; unless alignment does not change; then the same type `should` be returned
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for align in self.ALIGNMENTS:
            for t in types:
                src_align = align_of(t)
                new_t = align_as(t, align)
                if src_align == align:
                    # Allow it; but warn user
                    warnings.warn(UserWarning(f"{t.__class__}: `align_as` should not alter input `type-object` but a new `type-object` was returned!"))
                    # assert new_t is t, "`align_as` should not alter input `type-object` but a new `type-object` was returned!"
                else:
                    assert new_t is not t, "`align_as` should not alter input `type-object` but a new `type-object` was NOT returned!"

    def test_align_as_equality(self):
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for align in self.ALIGNMENTS:
            for t in types:
                src_align = align_of(t)
                new_t = align_as(t, align)
                redef_t = align_as(new_t, src_align)
                assert t == redef_t, "Same alignment should preserve equality of object!"

    def test_align_as_inequality(self):
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for align in self.ALIGNMENTS:
            for t in types:
                src_align = align_of(t)
                new_t = align_as(t, align)
                if src_align != align:
                    assert t != new_t, "Differing alignment should break equality of object!"
