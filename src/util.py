import struct
from typing import BinaryIO, Type, List


def validate_pack_args(func_name: str, count:int, args:List):
    if not count == len(args):
        struct.error(f"{func_name} expected {count} items for packing (got {len(args)})")


def validate_buffer_size(func_name: str, min_size:int, buffer):
    if isinstance(buffer, BinaryIO):
        check_buffer = buffer.read(min_size)
        buffer.seek(-min_size, 1)
        if len(check_buffer) < min_size:
            raise struct.error(f"{func_name} requires a buffer of at least {min_size} bytes")
    else:
        if len(buffer) < min_size:
            struct.error(f"{func_name} requires a buffer of at least {min_size} bytes")


def validate_buffer_size_offset(func_name: str, min_size:int, offset:int, buffer):
    if isinstance(buffer, BinaryIO):
        return_to = buffer.tell()
        buffer.seek(offset)
        check_buffer = buffer.read(min_size)
        buffer.seek(return_to)
        if len(check_buffer) < min_size:
            struct.error(f"{func_name} requires a buffer of at least {min_size} bytes at offset {offset} (actual buffer size is {len(check_buffer)})")
    else:
        b_offset = len(buffer) - offset
        b_offset = b_offset if b_offset > 0 else 0
        if b_offset < min_size:
            struct.error(f"{func_name} requires a buffer of at least {min_size} bytes at offset {offset} (actual buffer size is {b_offset})")


def validate_typing(cls, args, type_name: Type = bytes):
    if isinstance(type_name, list):
        for a in args:
            if not isinstance(a, tuple(type_name)):
                struct.error(f"arguments for '{cls.__name__}' must be an object from these types; {repr([t.__name__ for t in type_name])}")
    else:
        for a in args:
            if not isinstance(a, type_name):
                struct.error(f"arguments for '{cls.__name__}' must be a {type_name.__name__} object")


# https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod#:~:text=Class%20and%20instance%20methods%20live,will%20win%20in%20that%20case.&text=This%20is%20explicitly%20documented%3A,f()%20).
# BY Martijn Pieters

class hybridmethod:
    def __init__(self, fclass, finstance=None, doc=None):
        self.fclass = fclass
        self.finstance = finstance
        self.__doc__ = doc or fclass.__doc__
        # support use on abstract base classes
        self.__isabstractmethod__ = bool(
            getattr(fclass, '__isabstractmethod__', False)
        )

    def classmethod(self, fclass):
        return type(self)(fclass, self.finstance, None)

    def instancemethod(self, finstance):
        return type(self)(self.fclass, finstance, self.__doc__)

    def __get__(self, instance, cls):
        if instance is None or self.finstance is None:
            # either bound to the class, or no instance method available
            return self.fclass.__get__(cls, None)
        return self.finstance.__get__(instance, cls)
