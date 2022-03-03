import struct


class StructError(BaseException):
    ...


class StructPackingError(StructError):
    def __init__(self, func_name: str, expected_args: int, provided_args: int, *args):
        super().__init__(*args)
        self.func = func_name
        self.expected = expected_args
        self.provided = provided_args

    def __str__(self):
        return f"{self.func} expected {self.expected} items for packing (got {self.provided})"


class StructBufferSizeError(StructError):
    ...


class StructBufferTooSmallError(StructBufferSizeError):
    def __init__(self, func_name: str, fixed_size: int, var_sized: bool = False, *args):
        super().__init__(*args)
        self.func = func_name
        self.fixed_size = fixed_size
        self.is_var_size = var_sized

    def __str__(self):
        if self.is_var_size:
            return f"{self.func} requires a buffer of at least {self.fixed_size} bytes"
        else:
            return f"{self.func} requires a buffer of {self.fixed_size} bytes"


class StructOffsetBufferTooSmallError(StructBufferTooSmallError):
    def __init__(self, func_name: str, fixed_size: int, offset: int, buffer_size: int, var_sized: bool = False, *args):
        super().__init__(func_name, fixed_size, var_sized, *args)
        self.buffer_size = buffer_size
        self.offset = offset

    def __str__(self):
        if self.is_var_size:
            return f"{self.func} requires a buffer of at least {self.fixed_size} bytes at offset {self.offset} (actual buffer size is {self.buffer_size}"
        else:
            return f"{self.func} requires a buffer of {self.fixed_size} bytes at offset {self.offset} (actual buffer size is {self.buffer_size}"


class StructVarBufferTooSmallError(StructBufferTooSmallError):
    def __init__(self, func_name: str, var_size: int, buffer_size: int, *args):
        super().__init__(func_name, None, True, *args)
        self.buffer_size = buffer_size
        self.var_size = var_size

    def __str__(self):
        return f"{self.func} read a var-buffer of {self.var_size} bytes (expected var-buffer is {self.buffer_size})"

# class StructBufferTooBigError(StructBufferSizeError):
#     def __init__(self, func_name: str, fixed_size: int, var_sized: bool = False, strict_sized: bool = False, *args):
#         super().__init__(*args)
#         self.func = func_name
#         self.fixed_size = fixed_size
#         self.is_var_size = var_sized
#         self.strict_sized = strict_sized
#
#     def __str__(self):
#         return f"{self.func} requires a buffer of {self.fixed_size} bytes"
