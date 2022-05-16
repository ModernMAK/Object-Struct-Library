from typing import Protocol

from structlib.errors import ArgCountError


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
