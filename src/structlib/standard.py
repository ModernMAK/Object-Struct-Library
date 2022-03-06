import re
from struct import Struct
from typing import Tuple, Iterable, Optional, Union

from .core import StructObj, ByteLayoutFlag
from .types import UnpackResult, UnpackLenResult, BufferStream
from .util import hybridmethod, pack_into, pack_stream, unpack_stream, unpack, unpack_stream_with_len, unpack_with_len, unpack_from, unpack_from_with_len, iter_unpack

STANDARD_BOSA_MARKS = r"@=<>!"  # Byte Order, Size, Alignment
STANDARD_FMT_MARKS = r"xcbB?hHiIlLqQnNefdspP"


# Functions for common functionality on builtin structs


__struct_regex = re.compile(rf"([0-9]*)([{STANDARD_FMT_MARKS}])")  # 'x' is excluded because it is padding


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


class StandardStruct(StructObj):
    """
    A representation of a standard struct.Struct
    """
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

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        raise NotImplementedError

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_ARGS(cls) -> int:
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
    def fixed_size(self) -> int:
        return self.DEFAULT_LAYOUT.size

    @fixed_size.instancemethod
    @property
    def fixed_size(self) -> int:
        return self.__layout.size

    @hybridmethod
    @property
    def is_var_size(self) -> bool:
        return False

    @is_var_size.instancemethod
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
    def pack_into(cls, buffer, *args, offset: int = None) -> int:
        return pack_into(cls.DEFAULT_LAYOUT, buffer, *args, offset=offset)

    @pack_into.instancemethod
    def pack_into(self, buffer, *args, offset: int = None) -> int:
        return pack_into(self.__layout, buffer, *args, offset=offset)

    @hybridmethod
    def pack_stream(self, buffer: BufferStream, *args) -> int:
        return pack_stream(self.DEFAULT_LAYOUT, buffer, *args)

    @pack_stream.instancemethod
    def pack_stream(self, buffer: BufferStream, *args) -> int:
        return pack_stream(self.__layout, buffer, *args)

    @hybridmethod
    def unpack(self, buffer) -> UnpackResult:
        return unpack(self.DEFAULT_LAYOUT, buffer)

    @unpack.instancemethod
    def unpack(self, buffer) -> UnpackResult:
        return unpack(self.__layout, buffer)

    @hybridmethod
    def unpack_with_len(self, buffer) -> UnpackLenResult:
        return unpack_with_len(self.DEFAULT_LAYOUT, buffer)

    @unpack_with_len.instancemethod
    def unpack_with_len(self, buffer) -> UnpackLenResult:
        return unpack_with_len(self.__layout, buffer)

    @hybridmethod
    def unpack_from(self, buffer, offset: int = 0) -> UnpackResult:
        return unpack_from(self.DEFAULT_LAYOUT, buffer, offset)

    @unpack_from.instancemethod
    def unpack_from(self, buffer, offset: int = 0) -> UnpackResult:
        return unpack_from(self.__layout, buffer, offset)

    @hybridmethod
    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        return unpack_from_with_len(self.DEFAULT_LAYOUT, buffer, offset)

    @unpack_from_with_len.instancemethod
    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        return unpack_from_with_len(self.__layout, buffer, offset)

    @hybridmethod
    def unpack_stream(cls, buffer) -> UnpackResult:
        return unpack_from(cls.DEFAULT_LAYOUT, buffer)

    @unpack_stream.instancemethod
    def unpack_stream(self, buffer) -> UnpackResult:
        return unpack_from(self.__layout, buffer)

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return iter_unpack(self.DEFAULT_LAYOUT, buffer)

    @iter_unpack.instancemethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return iter_unpack(self.__layout, buffer)

    @hybridmethod
    def unpack_stream_with_len(self, buffer) -> UnpackLenResult:
        return unpack_stream_with_len(self.DEFAULT_LAYOUT, buffer)

    @unpack_stream_with_len.instancemethod
    def unpack_stream_with_len(self, buffer) -> UnpackLenResult:
        return unpack_stream_with_len(self.__layout, buffer)


class StructWrapper(StructObj):
    def __init__(self, s: Union[str, Struct]):
        if isinstance(s, str):
            s = Struct(s)
        self.__layout = s
        self.__args = _count_args(s.format)

    @property
    def fixed_size(self) -> int:
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
        return pack_into(self.__layout, buffer, *args, offset=offset)

    def pack_stream(self, buffer: BufferStream, *args) -> int:
        return pack_stream(self.__layout, buffer, *args)

    def unpack(self, buffer) -> UnpackResult:
        return unpack(self.__layout, buffer)

    def unpack_with_len(self, buffer) -> UnpackLenResult:
        return unpack_with_len(self.__layout, buffer)

    def unpack_from(self, buffer, offset: int = 0) -> UnpackResult:
        return unpack_from(self.__layout, buffer, offset)

    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        return unpack_from_with_len(self.__layout, buffer, offset)

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return iter_unpack(self.__layout, buffer)

    def unpack_stream(self, buffer: BufferStream) -> UnpackResult:
        return unpack_stream(self.__layout, buffer)

    def unpack_stream_with_len(self, buffer) -> UnpackLenResult:
        return unpack_stream_with_len(self.__layout, buffer)

    @property
    def format(self) -> str:
        return self.__layout.format


class Padding(StandardStruct):
    """ 
    Padding Byte(s) 
    
    For convenience, the class inherently represents a single pad byte.
    """
    DEFAULT_CODE = "x"

    __DEFAULT_LAYOUT = Struct("x")

    # noinspection PyPropertyDefinition
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


class Char(StandardStruct):
    DEFAULT_CODE = "c"

    __DEFAULT_LAYOUT = Struct("c")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "c", byte_layout_mark)


class Int8(StandardStruct):
    DEFAULT_CODE = "b"

    __DEFAULT_LAYOUT = Struct("b")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "b", byte_layout_mark)


class UInt8(StandardStruct):
    DEFAULT_CODE = "B"

    __DEFAULT_LAYOUT = Struct("B")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "B", byte_layout_mark)


class Boolean(StandardStruct):
    DEFAULT_CODE = "?"

    __DEFAULT_LAYOUT = Struct("?")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "?", byte_layout_mark)


class Int16(StandardStruct):
    DEFAULT_CODE = "h"

    __DEFAULT_LAYOUT = Struct("h")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "h", byte_layout_mark)


class UInt16(StandardStruct):
    DEFAULT_CODE = "H"

    __DEFAULT_LAYOUT = Struct("H")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "H", byte_layout_mark)


class Int32(StandardStruct):
    DEFAULT_CODE = "i"  # l

    __DEFAULT_LAYOUT = Struct("i")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "i", byte_layout_mark)


class UInt32(StandardStruct):
    DEFAULT_CODE = "I"  # L

    __DEFAULT_LAYOUT = Struct("I")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "I", byte_layout_mark)


class Int64(StandardStruct):
    DEFAULT_CODE = "q"  # l

    __DEFAULT_LAYOUT = Struct("q")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "q", byte_layout_mark)


class UInt64(StandardStruct):
    DEFAULT_CODE = "Q"  # L

    __DEFAULT_LAYOUT = Struct("Q")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "Q", byte_layout_mark)


# C Size-Type
class SSizeT(StandardStruct):
    DEFAULT_CODE = "n"

    __DEFAULT_LAYOUT = Struct("n")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "n", byte_layout_mark)


class SizeT(StandardStruct):
    DEFAULT_CODE = "N"

    __DEFAULT_LAYOUT = Struct("N")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "N", byte_layout_mark)


class Float16(StandardStruct):
    DEFAULT_CODE = "e"

    __DEFAULT_LAYOUT = Struct("e")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "e", byte_layout_mark)


class Float32(StandardStruct):
    DEFAULT_CODE = "f"

    __DEFAULT_LAYOUT = Struct("f")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "f", byte_layout_mark)


class Float64(StandardStruct):
    DEFAULT_CODE = "d"

    __DEFAULT_LAYOUT = Struct("d")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, byte_layout_mark: str = None):
        super().__init__(repeat, "d", byte_layout_mark)


class Bytes(StandardStruct):
    DEFAULT_CODE = "s"

    __DEFAULT_LAYOUT = Struct("s")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, size: int = None):
        super().__init__(repeat, "s", size)


class FixedPascalString(StandardStruct):
    DEFAULT_CODE = "p"

    __DEFAULT_LAYOUT = Struct("p")

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def DEFAULT_LAYOUT(cls) -> Struct:
        return cls.__DEFAULT_LAYOUT

    def __init__(self, repeat: int = 1, size: int = None, byte_layout_mark: str = None):
        super().__init__(repeat, "p", size, byte_layout_mark=byte_layout_mark)


class CPointer(StandardStruct):
    DEFAULT_CODE = "P"

    __DEFAULT_LAYOUT = Struct("P")

    # noinspection PyPropertyDefinition
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
# Struct allows l/L to substitute for Int32
struct_code2class["l"] = Int32
struct_code2class["L"] = UInt32

# ALIASES
# Int / Long can also be known as Long / LongLong; I'm going by C# keywords, but if there is any ambiguity, the underlying types are still available
Byte, SByte, Short, UShort, Int, UInt, Long, ULong, Half, Float, Double = UInt8, Int8, Int16, UInt16, Int32, UInt32, Int64, UInt64, Float16, Float32, Float64
