from __future__ import annotations
import re
from abc import ABC
from io import BytesIO
from struct import Struct
from typing import Tuple, Iterable, Optional, Union, Literal, Type, Any

from .core import StructObj, ByteLayoutFlag, StructObjHelper
from .error import StructPackingError, StructOffsetBufferTooSmallError, StructBufferTooSmallError
from .packer import calculate_padding, ByteFlags
from .types import UnpackResult, UnpackLenResult, BufferStream, BufferApiType, Buffer, BufferStreamTypes
from .util import hybridmethod, pack_into, pack_stream, unpack_stream, unpack, unpack_stream_with_len, unpack_with_len, unpack_from, unpack_from_with_len, iter_unpack, pack_into_stream

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


class HybridStructObjHelper(StructObjHelper):  # Mixin to simplify functionality for custom structs

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        raise NotImplementedError

    @property
    def _fixed_size(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def fixed_size(self) -> int:
        return self.default_instance._fixed_size

    @fixed_size.instancemethod
    @property
    def fixed_size(self) -> int:
        return self._fixed_size

    @property
    def _is_var_size(self) -> bool:
        raise NotImplementedError

    @hybridmethod
    @property
    def is_var_size(self) -> bool:
        return self.default_instance._is_var_size

    @is_var_size.instancemethod
    @property
    def is_var_size(self) -> bool:
        return self._is_var_size

    @property
    def _args(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def args(self) -> int:
        return self.default_instance._args

    @args.instancemethod
    @property
    def args(self) -> int:
        return self._args

    @property
    def _alignment(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def alignment(self) -> int:
        return self.default_instance._alignment

    @alignment.instancemethod
    @property
    def alignment(self) -> int:
        return self._alignment

    @property
    def _align(self) -> bool:
        raise NotImplementedError

    @hybridmethod
    @property
    def align(self) -> bool:
        return self.default_instance._align

    @align.instancemethod
    @property
    def align(self) -> bool:
        return self._align

    @hybridmethod
    def pack(self, *args) -> bytes:
        return self.default_instance.pack(*args)

    @pack.instancemethod
    def pack(self, *args) -> bytes:
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack.__name__, self.args, len(*args))
        return self._pack(*args)

    @hybridmethod
    def pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        return self.default_instance.pack_into(buffer, *args, offset=offset)

    @pack_into.instancemethod
    def pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_into.__name__, self.args, len(*args))
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.pack_into.__name__, self.fixed_size, offset, self._remaining(buffer,offset), self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._pack_into_stream(buffer, *args, offset=offset)
        else:
            return self._pack_into_buffer(buffer, *args, offset=offset)

    @hybridmethod
    def pack_stream(self, buffer: BufferStream, *args) -> int:
        return self.default_instance.pack_stream(buffer, *args)

    @pack_stream.instancemethod
    def pack_stream(self, buffer: BufferStream, *args) -> int:
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_stream.__name__, self.args, len(*args))
        return self._pack_stream(buffer, *args)

    @hybridmethod
    def unpack(self, buffer: Buffer) -> UnpackResult:
        return self.default_instance.unpack(buffer)

    @unpack.instancemethod
    def unpack(self, buffer: Buffer) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_stream(buffer)[1]
        else:
            return self._unpack_buffer(buffer)[1]

    @hybridmethod
    def unpack_with_len(self, buffer) -> UnpackLenResult:
        return self.default_instance.unpack_with_len(buffer)

    @unpack_with_len.instancemethod
    def unpack_with_len(self, buffer) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_with_len.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_stream(buffer)
        else:
            return self._unpack_buffer(buffer)

    @hybridmethod
    def unpack_stream(self, buffer: BufferStream) -> UnpackResult:
        return self.default_instance.unpack_stream(buffer)

    @unpack_stream.instancemethod
    def unpack_stream(self, buffer: BufferStream) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)[1]

    @hybridmethod
    def unpack_stream_with_len(self, buffer: BufferStream) -> UnpackLenResult:
        return self.default_instance.unpack_stream_with_len(buffer)

    @unpack_stream_with_len.instancemethod
    def unpack_stream_with_len(self, buffer: BufferStream) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream_with_len.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)

    @hybridmethod
    def unpack_from(self, buffer: Buffer, *, offset: int = None) -> UnpackResult:
        return self.default_instance.unpack_from(buffer, offset=offset)

    @unpack_from.instancemethod
    def unpack_from(self, buffer: Buffer, *, offset: int = None) -> UnpackResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_from_stream(buffer, offset=offset)[1]
        else:
            return self._unpack_from_buffer(buffer, offset=offset)[1]

    @hybridmethod
    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        return self.default_instance.unpack_from_with_len(buffer, offset=offset)

    @unpack_from_with_len.instancemethod
    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from_with_len.__name__, self.fixed_size, offset, self._remaining(buffer,offset), self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_from_stream(buffer, offset=offset)
        else:
            return self._unpack_from_buffer(buffer, offset=offset)

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[UnpackResult]:
        return self.default_instance.iter_unpack(buffer)

    @iter_unpack.instancemethod
    def iter_unpack(self, buffer) -> Iterable[UnpackResult]:
        if isinstance(buffer, BufferStreamTypes):
            return self._iter_unpack_stream(buffer)
        else:
            return self._iter_unpack_buffer(buffer)


class DefaultHybridMixin(StructObjHelper, ABC):

    def _pack_bytes(self, *args: Any) -> bytes:
        raise NotImplementedError

    def _unpack_bytes(self, buffer: BufferApiType) -> Tuple[Any, ...]:
        raise NotImplementedError

    def _pack(self, *args) -> bytes:
        return self._pack_bytes(*args)

    def _pack_into_stream(self, stream: BufferStream, *args, offset: int = None) -> int:
        return_to = stream.tell()
        if offset is not None:
            stream.seek(offset)
        padding = calculate_padding(stream.tell(), self.alignment) if self.align else 0
        if padding > 0:
            stream.write(bytes(b"\x00" * padding))
        to_write = self._pack_bytes(*args)
        stream.write(to_write)
        stream.seek(return_to)
        return len(to_write) + padding

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        offset = offset or 0
        padding = 0
        if self.align:
            padding = calculate_padding(offset, self.alignment)
            if padding > 0:
                buffer[offset:offset + padding] = bytes(b"\x00" * padding)
                offset += padding
        to_write = self._pack_bytes(*args)
        buffer[offset:offset + len(to_write)] = to_write[:]
        return len(to_write) + padding

    def _pack_stream(self, stream: BufferStream, *args) -> int:
        to_write = self._pack_bytes(*args)
        padding = calculate_padding(stream.tell(), self.alignment) if self.align else 0
        if padding > 0:
            stream.write(bytes(b"\x00" * padding))
        stream.write(to_write)
        return len(to_write) + padding

    def _unpack_buffer(self, buffer: BufferApiType) -> UnpackLenResult:
        return self.fixed_size, self._unpack_bytes(buffer)

    def _unpack_stream(self, stream: BufferStream) -> UnpackLenResult:
        padding = calculate_padding(stream.tell(), self.alignment) if self.align else 0
        if padding > 0:
            _ = stream.read(padding)
        f_size = self.fixed_size
        v_buffer = stream.read(f_size)
        return f_size + padding, self._unpack_bytes(v_buffer)

    def _unpack_from_buffer(self, buffer: BufferApiType, *, offset: int = None) -> UnpackLenResult:
        offset = offset or 0
        padding = calculate_padding(offset, self.alignment) if self.align else 0
        if padding > 0:
            offset += padding
        f_size = self.fixed_size
        read_buffer = buffer[offset:offset + f_size]
        read = self._unpack_bytes(read_buffer)
        return f_size + padding, read

    def _unpack_from_stream(self, stream: BufferStream, *, offset: int = None) -> UnpackLenResult:
        return_to = stream.tell()
        if offset is not None:
            stream.seek(offset)
        padding = calculate_padding(stream.tell(), self.alignment) if self.align else 0
        if padding > 0:
            _ = stream.read(padding)
        f_size = self.fixed_size
        read_buffer = stream.read(f_size)
        read = self._unpack_bytes(read_buffer)
        stream.seek(return_to)
        return f_size + padding, read

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[UnpackResult]:
        f_size = self.fixed_size
        offset = 0
        while offset < len(buffer):
            padding = calculate_padding(offset, self.alignment) if self.align else 0
            offset += padding
            read_buffer = buffer[offset:offset + f_size]
            offset += f_size
            yield self._unpack_bytes(read_buffer)

    def _iter_unpack_stream(self, stream: BufferStream) -> Iterable[UnpackResult]:
        f_size = self.fixed_size
        while True:
            sentinel = stream.read(1)
            if len(sentinel) != 1:
                break
            stream.seek(-1, 1)
            padding = calculate_padding(stream.tell(), self.alignment) if self.align else 0
            if padding > 0:
                _ = stream.read(padding)
            read_buffer = stream.read(f_size)
            yield self._unpack_bytes(read_buffer)


class _IntStruct(HybridStructObjHelper, DefaultHybridMixin, ABC):
    def __init__(self, args: int, size: int, signed: bool, flags: ByteFlags = ByteFlags.Aligned | ByteFlags.NativeEndian):
        self.__signed = signed
        self.__size = size
        self.__args = args
        self.__endian = flags.endian_literal
        self.__align = ByteFlags.Aligned in flags
        self.__flags = flags

    @property
    def _fixed_size(self) -> int:
        return self.__size * self.__args

    @property
    def _is_var_size(self) -> bool:
        return False

    @property
    def _alignment(self) -> int:
        return self.__size

    @property
    def _align(self) -> bool:
        return self.__align

    @property
    def _args(self) -> int:
        return self.__args

    def _pack_bytes(self, *args: int) -> bytes:
        with BytesIO() as buffer:
            for v in args:
                v_buf = int.to_bytes(v, self.__size, self.__endian, signed=self.__signed)
                buffer.write(v_buf)
            buffer.seek(0)
            return buffer.read()

    def _unpack_bytes(self, buffer: BufferApiType) -> Tuple[int, ...]:
        results = []
        for _ in range(self.__args):
            v_buf = buffer[_ * self.__size:(_ + 1) * self.__size]
            v = int.from_bytes(v_buf, self.__endian, signed=self.__signed)
            results.append(v)
        return tuple(results)


class Int8(_IntStruct):
    BUILTIN_STRUCT_CODE = "b"
    __BYTE_SIZE = 8 // 8
    __SIGNED = True

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class UInt8(_IntStruct):
    BUILTIN_STRUCT_CODE = "B"
    __BYTE_SIZE = 8 // 8
    __SIGNED = False

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class Int16(_IntStruct):
    BUILTIN_STRUCT_CODE = "h"
    __BYTE_SIZE = 16 // 8
    __SIGNED = True

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class UInt16(_IntStruct):
    BUILTIN_STRUCT_CODE = "H"
    __BYTE_SIZE = 16 // 8
    __SIGNED = False

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class Int32(_IntStruct):
    BUILTIN_STRUCT_CODE = "i"
    __BYTE_SIZE = 32 // 8
    __SIGNED = True

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class UInt32(_IntStruct):
    BUILTIN_STRUCT_CODE = "I"
    __BYTE_SIZE = 32 // 8
    __SIGNED = False

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class Int64(_IntStruct):
    BUILTIN_STRUCT_CODE = "q"
    __BYTE_SIZE = 64 // 8
    __SIGNED = True

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


class UInt64(_IntStruct):
    BUILTIN_STRUCT_CODE = "Q"
    __BYTE_SIZE = 64 // 8
    __SIGNED = False

    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.NativeEndian | ByteFlags.Aligned):
        super().__init__(args, self.__BYTE_SIZE, self.__SIGNED, flags)


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


class _FloatStruct(HybridStructObjHelper, DefaultHybridMixin, ABC):
    __ENDIAN_LITERAL2CODE = {'little': '<', 'big': '>'}
    __SIZE_VALUE2CODE = {2: 'e', 4: 'f', 8: 'd'}

    def __init__(self, args: int, size: int, flags: ByteFlags = ByteFlags.Aligned | ByteFlags.NativeEndian):
        self.__size = size
        self.__args = args
        self.__align = ByteFlags.Aligned in flags
        self.__flags = flags
        endian_code = self.__ENDIAN_LITERAL2CODE[flags.endian_literal]
        size_code = self.__SIZE_VALUE2CODE[self.__size]
        self.__struct = Struct(f"{endian_code} {self.__args}{size_code}")

    @property
    def _fixed_size(self) -> int:
        return self.__size * self.__args

    @property
    def _is_var_size(self) -> bool:
        return False

    @property
    def _alignment(self) -> int:
        return self.__size

    @property
    def _align(self) -> bool:
        return self.__align

    @property
    def _args(self) -> int:
        return self.__args

    def _pack_bytes(self, *args: float) -> bytes:
        return self.__struct.pack(*args)

    def _unpack_bytes(self, buffer: BufferApiType) -> Tuple[float, ...]:
        return self.__struct.unpack(buffer)


class Float16(_FloatStruct):
    BUILTIN_STRUCT_CODE = "e"
    __BYTE_SIZE = 16 // 8

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.Aligned | ByteFlags.NativeEndian):
        super().__init__(args, self.__BYTE_SIZE, flags)


class Float32(_FloatStruct):
    BUILTIN_STRUCT_CODE = "f"
    __BYTE_SIZE = 32 // 8

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.Aligned | ByteFlags.NativeEndian):
        super().__init__(args, self.__BYTE_SIZE, flags)


class Float64(_FloatStruct):
    BUILTIN_STRUCT_CODE = "d"
    __BYTE_SIZE = 64 // 8

    # noinspection PyPropertyDefinition
    @classmethod
    @property
    def default_instance(cls) -> HybridStructObjHelper:
        return cls()

    def __init__(self, args: int = 1, flags: ByteFlags = ByteFlags.Aligned | ByteFlags.NativeEndian):
        super().__init__(args, self.__BYTE_SIZE, flags)


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
for c in [Padding, Char, Bytes, Boolean, SSizeT, SizeT, FixedPascalString, CPointer]:
    struct_code2class[c.DEFAULT_CODE] = c
for c in [Int8, UInt8, Int16, UInt16, Int32, UInt32, Int64, UInt64,  Float16, Float32, Float64,]:
    struct_code2class[c.BUILTIN_STRUCT_CODE] = c

# Struct allows l/L to substitute for Int32
struct_code2class["l"] = Int32
struct_code2class["L"] = UInt32

# ALIASES
# Int / Long can also be known as Long / LongLong; I'm going by C# keywords, but if there is any ambiguity, the underlying types are still available
Byte, SByte, Short, UShort, Int, UInt, Long, ULong, Half, Float, Double = UInt8, Int8, Int16, UInt16, Int32, UInt32, Int64, UInt64, Float16, Float32, Float64
