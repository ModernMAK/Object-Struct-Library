import re
from struct import Struct
from typing import Tuple, Iterable, Optional, BinaryIO, Union

from core import ObjStructField, ByteLayoutFlag
from util import hybridmethod

STANDARD_BOSA_MARKS = r"@=<>!"  # Byte Order, Size, Alignment
STANDARD_FMT_MARKS = r"xcbB?hHiIlLqQnNefdspP"


def _pack_into(layout: Struct, buffer, offset: int, *args) -> int:
    if isinstance(buffer, BinaryIO):
        # We mirror pack_into, but for a stream; offset is always relative to start because of this
        return_to = buffer.tell()
        buffer.seek(offset)
        result = layout.pack(*args)
        buffer.write(result)
        buffer.seek(return_to)
        return layout.size
    else:
        layout.pack_into(buffer, offset, *args)
        return layout.size


def _pack_stream(layout: Struct, buffer: BinaryIO, *args) -> int:
    result = layout.pack(*args)
    return buffer.write(result)


def _unpack(layout: Struct, buffer) -> Tuple:
    if isinstance(buffer, BinaryIO):
        buffer = buffer.read(layout.size)
    return layout.unpack(buffer)


def _unpack_from(layout: Struct, buffer, offset: int = 0) -> Tuple:
    if isinstance(buffer, BinaryIO):
        return_to = buffer.tell()
        buffer.seek(offset)
        stream_buffer = buffer.read(layout.size)
        result = layout.unpack(stream_buffer)
        buffer.seek(return_to)
        return result
    else:
        return layout.unpack_from(buffer, offset)


def _unpack_stream(layout: Struct, buffer: BinaryIO) -> Tuple:
    stream_buffer = buffer.read(layout.size)
    return layout.unpack(stream_buffer)


def _iter_unpack(layout: Struct, buffer) -> Iterable[Tuple]:
    if isinstance(buffer, BinaryIO):
        if layout.size == 0:
            raise ValueError("Layout has no size?!")
        while True:
            stream_buffer = buffer.read(layout.size)
            if len(stream_buffer) == 0:
                break
            yield layout.unpack(stream_buffer)
    else:
        return layout.iter_unpack(buffer)


__struct_regex = re.compile(rf"(?:([0-9]*)([{STANDARD_FMT_MARKS}]))")  # 'x' is excluded because it is padding
def _count_args(fmt: str) -> int:
    count = 0
    pos = 0
    while pos < len(fmt):
        match = __struct_regex.search(fmt, pos)
        if match is None:
            break
        else:
            repeat = match.group(1)
            code = match.group(2)
            if code == "s":
                count += 1
            else:
                count += int(repeat) if repeat else 1
            pos = match.span()[1]
    return count

class _StandardStruct(ObjStructField):
    """
    A representation of a standard struct.Struct
    """
    IS_STANDARD_STRUCT = True
    __DEF_FLAG = ByteLayoutFlag.NativeSize | ByteLayoutFlag.NativeEndian | ByteLayoutFlag.NativeAlignment
    __BLM_FLAG_MAP = {
        "@": ByteLayoutFlag.NativeSize | ByteLayoutFlag.NativeEndian | ByteLayoutFlag.NativeAlignment,
        "=": ByteLayoutFlag.StandardSize | ByteLayoutFlag.NativeEndian | ByteLayoutFlag.NoAlignment,
        "<": ByteLayoutFlag.StandardSize | ByteLayoutFlag.LittleEndian | ByteLayoutFlag.NoAlignment,
        ">": ByteLayoutFlag.StandardSize | ByteLayoutFlag.BigEndian | ByteLayoutFlag.NoAlignment,
        "!": ByteLayoutFlag.StandardSize | ByteLayoutFlag.NetworkEndian | ByteLayoutFlag.NoAlignment,
    }

    def __init__(self, repeat: int, code: str, repeat_size: int = None, byte_layout_mark: str = None):
        self.__repeat = repeat
        fmt_str = f"{repeat if repeat > 1 else ''}{code}"
        if repeat_size:  # used for special case: string, where repeat is used for string length
            fmt_str = " ".join(fmt_str for _ in range(repeat_size))
        if byte_layout_mark:
            fmt_str = byte_layout_mark + fmt_str
        self.__layout = Struct(fmt_str)
        self.__flags = self.__BLM_FLAG_MAP[byte_layout_mark] if byte_layout_mark else None

    @hybridmethod
    @property
    def byte_flags(self) -> None:
        return None

    @byte_flags.instancemethod
    @property
    def byte_flags(self) -> Optional[ByteLayoutFlag]:
        """
        The flags this structure was created with, if None, no flags were specified.

        :return: Flags if the struct specified them, None otherwise.
        """
        return self.__flags

    @classmethod
    @property
    def DEFAULT_LAYOUT(self) -> Struct:
        raise NotImplementedError

    @classmethod
    @property
    def DEFAULT_ARGS(self) -> int:
        return 1

    @hybridmethod
    @property
    def format(self) -> str:
        return self.DEFAULT_LAYOUT.format

    @format.instancemethod
    @property
    def format(self) -> str:
        return self.__layout.format

    @hybridmethod
    @property
    def size(self) -> int:
        return self.DEFAULT_LAYOUT.size

    @size.instancemethod
    @property
    def size(self) -> int:
        return self.__layout.size

    @hybridmethod
    @property
    def min_size(self) -> int:
        return self.DEFAULT_LAYOUT.size

    @min_size.instancemethod
    @property
    def min_size(self) -> int:
        return self.__layout.size

    @property
    def is_var_size(self) -> bool:
        return False

    @hybridmethod
    @property
    def args(self) -> int:
        return self.DEFAULT_ARGS

    @args.instancemethod
    @property
    def args(self) -> int:
        return self.__repeat

    @hybridmethod
    def pack(self, *args) -> bytes:
        return self.DEFAULT_LAYOUT.pack(*args)

    @pack.instancemethod
    def pack(self, *args) -> bytes:
        return self.__layout.pack(*args)

    @hybridmethod
    def pack_into(self, buffer, offset: int, *args) -> int:
        return _pack_into(self.DEFAULT_LAYOUT, buffer, *args, offset)

    @pack.instancemethod
    def pack_into(self, buffer, offset: int, *args) -> int:
        return _pack_into(self.__layout, buffer, *args, offset)

    @hybridmethod
    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        return _pack_stream(self.DEFAULT_LAYOUT, buffer, *args)

    @pack.instancemethod
    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        return _pack_stream(self.__layout, buffer, *args)

    @hybridmethod
    def unpack(self, buffer) -> Tuple:
        return _unpack(self.DEFAULT_LAYOUT, buffer)

    @unpack.instancemethod
    def unpack(self, buffer) -> Tuple:
        return _unpack(self.__layout, buffer)

    @hybridmethod
    def unpack_from(self, buffer, offset: int = 0) -> Tuple:
        return _unpack_from(self.DEFAULT_LAYOUT, buffer, offset)

    @unpack.instancemethod
    def unpack_from(self, buffer, offset: int = 0) -> Tuple:
        return _unpack_from(self.__layout, buffer, offset)

    @hybridmethod
    def unpack_stream(self, buffer) -> Tuple:
        return _unpack_from(self.DEFAULT_LAYOUT, buffer)

    @unpack.instancemethod
    def unpack_stream(self, buffer) -> Tuple:
        return _unpack_from(self.__layout, buffer)

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return _iter_unpack(self.DEFAULT_LAYOUT, buffer)

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return _iter_unpack(self.__layout, buffer)


class StructWrapper(ObjStructField):
    IS_STANDARD_STRUCT = True

    def __init__(self, s: Union[str, Struct]):
        if isinstance(s, str):
            s = Struct(s)
        self.__layout = s
        self.__args = _count_args(s.format)

    @property
    def size(self) -> int:
        return self.__layout.size

    @property
    def min_size(self) -> int:
        return self.__layout.size

    @property
    def args(self) -> int:
        return self.__layout.size

    @property
    def is_var_size(self) -> bool:
        return False

    def pack(self, *args) -> bytes:
        return self.__layout.pack(*args)

    def pack_into(self, buffer, *args, offset: int = 0) -> int:
        return _pack_into(self.__layout, buffer, *args)

    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        return _pack_stream(self.__layout, buffer, *args)

    def unpack(self, buffer) -> Tuple:
        return _unpack(self.__layout, buffer)

    def unpack_from(self, buffer, offset: int = 0) -> Tuple:
        return _unpack_stream(self.__layout, buffer)

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return _iter_unpack(self.__layout, buffer)

    def unpack_stream(self, buffer: BinaryIO) -> Tuple:
        return _unpack_stream(self.__layout, buffer)

    @property
    def format(self) -> str:
        return self.__layout.format


class Padding(_StandardStruct):
    """ 
    Padding Byte(s) 
    
    For convenience, the class inherently represents a single pad byte.
    """
    DEFAULT_CODE = "x"

    __DEFAULT_LAYOUT = Struct("x")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "x", byte_layout_mark)

    @hybridmethod
    @property
    def args(self) -> int:
        return 0

    @args.instancemethod
    @property
    def args(self) -> int:
        return 0


class Char(_StandardStruct):
    DEFAULT_CODE = "c"

    __DEFAULT_LAYOUT = Struct("c")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "c", byte_layout_mark)


class Int8(_StandardStruct):
    DEFAULT_CODE = "b"

    __DEFAULT_LAYOUT = Struct("b")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "b", byte_layout_mark)


class UInt8(_StandardStruct):
    DEFAULT_CODE = "B"

    __DEFAULT_LAYOUT = Struct("B")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "B", byte_layout_mark)


class Boolean(_StandardStruct):
    DEFAULT_CODE = "?"

    __DEFAULT_LAYOUT = Struct("?")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "?", byte_layout_mark)


class Int16(_StandardStruct):
    DEFAULT_CODE = "h"

    __DEFAULT_LAYOUT = Struct("h")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "h", byte_layout_mark)


class UInt16(_StandardStruct):
    DEFAULT_CODE = "H"

    __DEFAULT_LAYOUT = Struct("H")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "H", byte_layout_mark)


class Int32(_StandardStruct):
    DEFAULT_CODE = "i"  # l

    __DEFAULT_LAYOUT = Struct("i")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "i", byte_layout_mark)


class UInt32(_StandardStruct):
    DEFAULT_CODE = "I"  # L

    __DEFAULT_LAYOUT = Struct("I")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "I", byte_layout_mark)


class Int64(_StandardStruct):
    DEFAULT_CODE = "q"  # l

    __DEFAULT_LAYOUT = Struct("q")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "q", byte_layout_mark)


class UInt64(_StandardStruct):
    DEFAULT_CODE = "Q"  # L

    __DEFAULT_LAYOUT = Struct("Q")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "Q", byte_layout_mark)


# C Size-Type
class SSizeT(_StandardStruct):
    DEFAULT_CODE = "n"

    __DEFAULT_LAYOUT = Struct("n")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "n", byte_layout_mark)


class SizeT(_StandardStruct):
    DEFAULT_CODE = "N"

    __DEFAULT_LAYOUT = Struct("N")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "N", byte_layout_mark)


class Float16(_StandardStruct):
    DEFAULT_CODE = "e"

    __DEFAULT_LAYOUT = Struct("e")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "e", byte_layout_mark)


class Float32(_StandardStruct):
    DEFAULT_CODE = "f"

    __DEFAULT_LAYOUT = Struct("f")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "f", byte_layout_mark)


class Float64(_StandardStruct):
    DEFAULT_CODE = "d"

    __DEFAULT_LAYOUT = Struct("d")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "d", byte_layout_mark)


class Bytes(_StandardStruct):
    DEFAULT_CODE = "s"

    __DEFAULT_LAYOUT = Struct("s")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, size: int = None):
        super().__init__(repeat, "s", size)


class FixedPascalString(_StandardStruct):
    DEFAULT_CODE = "p"

    __DEFAULT_LAYOUT = Struct("p")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, size: int = None, byte_layout_mark: str = None):
        super().__init__(repeat, "p", size, byte_layout_mark=byte_layout_mark)


class CPointer(_StandardStruct):
    DEFAULT_CODE = "P"

    __DEFAULT_LAYOUT = Struct("P")

    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "P", byte_layout_mark=byte_layout_mark)


struct_code2class = {
}
for c in [Padding, Char, Int8, UInt8, Bytes, Boolean, Int16, UInt16, Int32, UInt32, Int64, UInt64, SSizeT, SizeT, Float16, Float32, Float64, FixedPascalString, CPointer]:
    struct_code2class[c.DEFAULT_CODE] = c
struct_code2class["l"] = Int32
struct_code2class["L"] = UInt32

# ALIASES

Byte, SByte, Short, UShort, Int, UInt, Long, ULong, Half, Float, Double = UInt8, Int8, Int16, UInt16, Int32, UInt32, Int64, UInt64, Float16, Float32, Float64

