from typing import Protocol

from structlib.errors import FixedBufferSizeError


class SizeLike(Protocol):
    """
    Exposes the fixed size of a struct
    """

    @property
    def _size_(self) -> int:
        """
        The fixed size of the struct
        """
        ...


class SizeLikeMixin:
    def __init__(self, size: int):
        if size < 1:
            raise ValueError("Size cannot be < 1! (What struct has no size? Var-sized types should not use SizeLike; this is a FIXED SIZE!)")
        self.__size = size

    @property
    def _size_(self) -> int:
        return self.__size

    def __eq__(self, other) -> bool:
        if not isinstance(other, SizeLikeMixin):
            return False
        else:
            return self.__size == other.__size

    def assert_size(self, given_size: int):
        expected_size = size_of(self)
        if expected_size != given_size:
            raise FixedBufferSizeError(expected_size, given_size)


def size_of(sizeable: SizeLike) -> int:
    return sizeable._size_
