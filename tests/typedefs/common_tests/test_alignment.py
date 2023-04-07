import warnings
from typing import List

from structlib.typedef import TypeDefAlignable, align_of, align_as
from tests.typedefs.util import classproperty


# AVOID using test as prefix
class AlignmentTests:
    """
    Represents a container for testing an BooleanDefinition
    """

    @classproperty
    def ALIGNMENTS(self) -> List[int]:
        raise NotImplementedError

    @classproperty
    def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
        raise NotImplementedError

    def test_align_as(self):
        types = self.ALIGNABLE_TYPEDEFS
        for align in self.ALIGNMENTS:
            for t in types:
                new_t = align_as(t, align)
                assert align_of(new_t) == align, "`align_of` not getting value set by `align_as`!"

    def test_align_as_preserves_type(self):
        # A new types should be returned by align_as; unless alignment does not change; then the same type `should` be returned
        types = self.ALIGNABLE_TYPEDEFS
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
        types = self.ALIGNABLE_TYPEDEFS
        for align in self.ALIGNMENTS:
            for t in types:
                src_align = align_of(t)
                new_t = align_as(t, align)
                redef_t = align_as(new_t, src_align)
                assert t == redef_t, "Same alignment should preserve equality of object!"

    def test_align_as_inequality(self):
        types = self.ALIGNABLE_TYPEDEFS
        for align in self.ALIGNMENTS:
            for t in types:
                src_align = align_of(t)
                new_t = align_as(t, align)
                if src_align != align:
                    assert t != new_t, "Differing alignment should break equality of object!"
