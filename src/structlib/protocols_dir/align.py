from typing import Protocol, Optional

from structlib.errors import StructError
from structlib.helper import default_if_none


class AlignmentError(StructError):
    ...


class AlignLike(Protocol):
    """
    Exposes the alignment of a struct
    """

    @property
    def _align_(self) -> int:
        """
        The alignment (in bytes) the struct will align to
        """
        ...

    @_align_.setter
    def _align_(self, alignment: int) -> None:
        """
        Sets the alignment of this type.
        :param alignment: The desired alignment (in bytes) the struct will align to
        """
        ...


# Not technically a mixin
#   Super cannot be auto-called because we have arguments
class Alignable:
    def __init__(self, align_as: int, default_align: int = None):
        self.__alignment = self.resolve_alignment(align_as, default_align)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Alignable):
            return False
        else:
            return self.__alignment == other.__alignment

    @property
    def _align_(self) -> int:
        return self.__alignment

    @_align_.setter
    def _align_(self, alignment: int) -> None:
        self.__alignment = self.resolve_alignment(alignment)

    @staticmethod
    def resolve_alignment(align_as: Optional[int], default_align: Optional[int] = None) -> int:
        """
        Returns the alignment (align_as if specified; otherwise default_align)
        If the alignment is invalid (None or `alignment < 1`) an AlignmentError is raised
        :param align_as: The desired alignment to use; None will use default_align
        :param default_align: The default alignment ot use; None will raise an AlignmentError if align_as is None
        :return: The alignment in bytes; an integer >= 1
        """
        alignment = default_if_none(align_as, default_align)
        if alignment is None:
            raise AlignmentError("No alignment specified!")
        if alignment <= 0:
            raise AlignmentError("Alignment cannot be <= 0!")
        return alignment


def align_of(alignable: AlignLike) -> int:
    return alignable._align_


def align_as(alignable: AlignLike, alignment: int):
    alignable._align_ = alignment
    return alignable
