from typing import Protocol

from structlib.errors import StructError


class FixedBufferSizeError(StructError):
    def __init__(self, buf_size: int, expected_size: int):
        self.buf_size = buf_size
        self.expected_size = expected_size

    def __str__(self):
        return f"Buffer is '{self.buf_size}' bytes, expected '{self.expected_size}' bytes!"


class ArgCountError(StructError):
    def __init__(self, given: int, expected: int):
        self.given = given
        self.expected = expected

    def __str__(self):
        return f"Received '{self.given}' args, expected '{self.expected}' args!"


class ArgLike(Protocol):
    """
    The # of fields this structure holds
    """

    def _args_(self) -> int:
        """ The # of fields this structure expects """
        ...


class ArgLikeMixin:
    def __init__(self, args: int):
        self.__args = args

    def _args_(self) -> int:
        return self.__args

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArgLikeMixin):
            return False
        else:
            return self.__args == other.__args

    def assert_args(self, given_args: int):
        expected_args = self._args_()
        if expected_args != given_args:
            raise ArgCountError(given_args, expected_args)
