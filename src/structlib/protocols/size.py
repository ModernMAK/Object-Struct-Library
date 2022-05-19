from typing import Protocol, Optional

from structlib.errors import StructError


class VarSizeError(StructError):
    def __str__(self):
        return "This struct has a variable size!"


class FixedBufferSizeError(StructError):
    def __init__(self, buf_size: int, expected_size: int):
        self.buf_size = buf_size
        self.expected_size = expected_size

    def __str__(self):
        return f"Buffer is '{self.buf_size}' bytes, expected '{self.expected_size}' bytes!"


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


class VarSizeLikeMixin:
    def __init__(self, size: Optional[int] = None):
        if size is not None and size < 1:
            raise ValueError(f"Size '{size}' cannot be < 1! (What struct has no size? Var-sized types should use VarSizeLike instead)")
        self.__size = size

    @property
    def _size_(self) -> int:
        if self.__size is None:
            raise VarSizeError
        return self.__size

    @property
    def is_fixed_size(self):
        return self.__size is not None

    def __eq__(self, other) -> bool:
        if not isinstance(other, VarSizeLikeMixin):
            return False
        else:
            return self.__size == other.__size

    def assert_size(self, given_size: int):
        if self.__size is not None:
            expected_size = size_of(self)
            if expected_size != given_size:
                raise FixedBufferSizeError(expected_size, given_size)


class SizeLikeMixin:
    def __init__(self, size: int):
        if size < 1:
            raise ValueError("Size cannot be < 1! (What struct has no size? Var-sized types should use VarSizeLike instead)")
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
