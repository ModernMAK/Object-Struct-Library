from collections import Callable


class StructError(Exception):
    ...


class UnpackError(StructError):
    ...


class PackError(StructError):
    ...


class ArgTypeError(PackError):
    ...

class ArgCountError(PackError):
    def __init__(self, given: int, expected: int):
        self.given = given
        self.expected = expected

    def __str__(self):
        return f"Received '{self.given}' args, expected '{self.expected}' args!"

class FixedBufferSizeError(StructError):
    def __init__(self, buf_size: int, expected_size: int):
        self.buf_size = buf_size
        self.expected_size = expected_size

    def __str__(self):
        return f"Buffer is '{self.buf_size}' bytes, expected '{self.expected_size}' bytes!"


class UnpackBufferSizeError(UnpackError):
    def __init__(self, func_name: str, buf_size: int, expected_size: int):
        self.func_name = func_name
        self.buf_size = buf_size
        self.expected_size = expected_size

    def __str__(self):
        return f"'{self.func_name}' received a buffer with '{self.buf_size}', expected '{self.expected_size}'!"
