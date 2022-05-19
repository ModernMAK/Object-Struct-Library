class StructError(Exception):
    ...


class UnpackError(StructError):
    ...


class PackError(StructError):
    ...


class ArgTypeError(PackError):
    ...



class UnpackBufferSizeError(UnpackError):
    def __init__(self, func_name: str, buf_size: int, expected_size: int):
        self.func_name = func_name
        self.buf_size = buf_size
        self.expected_size = expected_size

    def __str__(self):
        return f"'{self.func_name}' received a buffer with '{self.buf_size}', expected '{self.expected_size}'!"
