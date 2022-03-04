from enum import Flag
from io import BytesIO
from mmap import mmap
from typing import Tuple, Iterable, List, BinaryIO, Union, Type, Optional, Any

from .error import StructPackingError, StructOffsetBufferTooSmallError, StructBufferTooSmallError

BufferStream = Union[BytesIO, BinaryIO]  # TODO, better solution!?
BufferStreamTypes = (BytesIO, BinaryIO)
BufferApiType = Union[bytes, bytearray, mmap]
Buffer = Union[BufferStream, BufferApiType]
UnpackResult = Tuple[Any, ...]
UnpackLenResult = Tuple[int, UnpackResult]


class ByteLayoutFlag(Flag):
    NativeEndian = 0b00
    NetworkEndian = 0b01
    LittleEndian = 0b10
    BigEndian = 0b11

    NativeSize = 0b000
    StandardSize = 0b100

    NativeAlignment = 0b0000
    NoAlignment = 0b1000


class ObjStruct:
    # Things of note; we don't use format anymore; because that couples it to a string, which we'd preferably use a converter-mapping for
    # Also we now only use one size; fixed_size, which is the fixed_size of a variable_size structure or the total size in a fixed_size structure

    @property
    def fixed_size(self) -> int:
        """ The fixed size of the buffer """
        raise NotImplementedError

    @property
    def args(self) -> int:
        """
        The number of arguments this struct expects
        :return:
        """
        raise NotImplementedError

    @property
    def is_var_size(self) -> bool:
        raise NotImplementedError

    def pack(self, *args) -> bytes:
        raise NotImplementedError

    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        raise NotImplementedError

    def pack_into(self, buffer, *args, offset: int = None) -> int:
        raise NotImplementedError

    def unpack(self, buffer) -> UnpackResult:
        raise NotImplementedError

    def unpack_with_len(self, buffer) -> UnpackLenResult:
        raise NotImplementedError

    def unpack_stream(self, buffer: BinaryIO) -> UnpackResult:
        raise NotImplementedError

    def unpack_stream_with_len(self, buffer) -> UnpackLenResult:
        raise NotImplementedError

    def unpack_from(self, buffer, offset: int = None) -> UnpackResult:  # known case of _struct.Struct.unpack_from
        """
        Return a tuple containing unpacked values.

        Values are unpacked according to the format string Struct.format.

        The buffer's size in bytes, starting at position offset, must be
        at least Struct.size.

        See help(struct) for more on format strings.
        """
        raise NotImplementedError

    def unpack_from_with_len(self, buffer, offset: int = None) -> UnpackLenResult:
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError


class ObjStructHelper(ObjStruct):  # Mixin to simplify functionality for custom structs
    @property
    def fixed_size(self) -> int:
        raise NotImplementedError

    @property
    def is_var_size(self) -> bool:
        raise NotImplementedError

    @property
    def args(self) -> int:
        raise NotImplementedError

    def _arg_count_mismatch(self, *args) -> bool:
        return len(args) != self.args

    def _buffer_too_small(self, buffer: BufferApiType, offset: int = None) -> bool:
        size = len(buffer) - (offset or 0)
        return size < self.fixed_size

    def _arg_types(self) -> Optional[Union[Type, Tuple[Type, ...]]]:
        return None

    def _arg_type_mismatch(self, *args) -> bool:
        types = self._arg_types()
        if types is None:
            return False
        # if isinstance(types, list):
        #     msg = f"arguments for '{cls.__name__}' must be an object from these types; {repr([t.__name__ for t in type_name])}"
        # else:
        #     msg = f"arguments for '{cls.__name__}' must be a {type_name.__name__} object"
        return any(not isinstance(a, types) for a in args)

    def _stream_too_small(self, stream: BinaryIO, offset: int = None) -> bool:
        if offset:
            return_to = stream.tell()
            stream.seek(offset)
            read = stream.read(self.fixed_size)
            stream.seek(return_to)
        else:
            read = stream.read(self.fixed_size)
            stream.seek(-self.fixed_size, 1)
        return len(read) < self.fixed_size

    def _too_small(self, buffer: Buffer, offset: int = None) -> bool:
        if isinstance(buffer, BinaryIO):
            return self._stream_too_small(buffer, offset=offset)
        else:
            return self._buffer_too_small(buffer, offset=offset)

    def _pack(self, *args) -> bytes:
        raise NotImplementedError

    def pack(self, *args) -> bytes:
        # Repeat to have errors in proper places
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack.__name__, self.args, len(*args))
        return self._pack(*args)

    def _pack_into_stream(self, stream: BinaryIO, *args, offset: int = None) -> int:
        raise NotImplementedError

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        raise NotImplementedError

    def pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        # Repeat to have errors in proper places
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_into.__name__, self.args, len(*args))
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.pack_into.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BinaryIO):
            return self._pack_into_stream(buffer, *args, offset=offset)
        else:
            return self._pack_into_buffer(buffer, *args, offset=offset)

    def _pack_stream(self, buffer: BinaryIO, *args) -> int:
        raise NotImplementedError

    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        # Repeat to have errors in proper places
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_stream.__name__, self.args, len(*args))
        return self._pack_stream(buffer, *args)

    def _unpack_buffer(self, buffer: BufferApiType) -> UnpackLenResult:
        raise NotImplementedError

    def _unpack_stream(self, stream: BinaryIO) -> UnpackLenResult:
        raise NotImplementedError

    def unpack(self, buffer: Buffer) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BinaryIO):
            return self._unpack_stream(buffer)[1]
        else:
            return self._unpack_buffer(buffer)[1]

    def unpack_with_len(self, buffer) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_with_len.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BinaryIO):
            return self._unpack_stream(buffer)
        else:
            return self._unpack_buffer(buffer)

    def unpack_stream(self, buffer: BinaryIO) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)[1]

    def unpack_stream_with_len(self, buffer: BinaryIO) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream_with_len.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)

    def _unpack_from_buffer(self, buffer: BufferApiType, *, offset: int = None) -> UnpackLenResult:
        raise NotImplementedError

    def _unpack_from_stream(self, stream: BinaryIO, *, offset: int = None) -> UnpackLenResult:
        raise NotImplementedError

    def unpack_from(self, buffer: Buffer, *, offset: int = None) -> UnpackResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BinaryIO):
            return self._unpack_from_stream(buffer, offset=offset)[1]
        else:
            return self._unpack_from_buffer(buffer, offset=offset)[1]

    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from_with_len.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BinaryIO):
            return self._unpack_from_stream(buffer, offset=offset)
        else:
            return self._unpack_from_buffer(buffer, offset=offset)

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[Tuple]:
        raise NotImplementedError

    def _iter_unpack_stream(self, stream: BinaryIO) -> Iterable[Tuple]:
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        if isinstance(buffer, BinaryIO):
            return self._iter_unpack_stream(buffer)
        else:
            return self._iter_unpack_buffer(buffer)


class MultiStruct(ObjStructHelper):
    def __init__(self, *structures: Union[ObjStruct, Type[ObjStruct]]):
        sub_layouts = structures or []
        self.__is_var_size = any(s.is_var_size for s in sub_layouts)
        self.__size = sum(s.fixed_size for s in sub_layouts)
        self.__args = sum(1 if isinstance(s, MultiStruct) else s.args for s in sub_layouts)
        self.__sub_layouts: List[Tuple[ObjStruct, bool]] = [(s, isinstance(s, MultiStruct)) for s in sub_layouts]

    @property
    def fixed_size(self) -> int:
        return self.__size

    @property
    def is_var_size(self) -> bool:
        return self.__is_var_size

    @classmethod
    def __get_args(cls, s: ObjStruct) -> int:
        """Gets the # of args for a flat struct, or 1 for a MultiStruct"""
        return 1 if isinstance(s, MultiStruct) else s.args

    @property
    def args(self) -> int:
        return self.__args

    def _pack(self, *args) -> bytes:
        with BytesIO() as buffer:
            self._pack_stream(buffer, *args)
        buffer.seek(0)
        return buffer.read()

    def _pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        arg_off = 0
        written = 0
        for child, nested in self.__sub_layouts:
            arg_c = 1 if nested else child.args
            child_args = args[arg_off:arg_off + arg_c]
            arg_off += arg_c
            written += child.pack_into(buffer, *child_args, offset=offset)
        return written

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        return self._pack_into(buffer, *args, offset=offset)

    def _pack_into_stream(self, buffer: BinaryIO, *args, offset: int = None) -> int:
        return self._pack_into(buffer, *args, offset=offset)

    def _pack_stream(self, buffer: BinaryIO, *args) -> int:
        arg_off = 0
        written = 0
        for child, nested in self.__sub_layouts:
            arg_c = 1 if nested else child.args
            child_args = args[arg_off:arg_off + arg_c]
            arg_off += arg_c
            written += child.pack_stream(buffer, *child_args)
        return written

    def _unpack_buffer(self, buffer: BufferApiType) -> UnpackLenResult:
        total_read = 0
        results = []
        for child, nested in self.__sub_layouts:
            read, r = child.unpack_from_with_len(buffer, offset=total_read)
            if nested:
                results.append(r)
            else:
                results.extend(r)
            total_read += read
        return total_read, tuple(results)

    def _unpack_stream(self, stream: BinaryIO) -> UnpackLenResult:
        total_read = 0
        results = []
        for child, nested in self.__sub_layouts:
            read, r = child.unpack_stream_with_len(stream)
            if nested:
                results.append(r)
            else:
                results.extend(r)
            total_read += read
        return total_read, tuple(results)

    def _unpack_from_buffer(self, buffer: BufferApiType, *, offset: int = None) -> UnpackLenResult:
        return self._unpack_from(buffer, offset=offset)

    def _unpack_from_stream(self, stream: BinaryIO, *, offset: int = None) -> UnpackLenResult:
        return self._unpack_from(stream, offset=offset)

    def _unpack_from(self, buffer: Buffer, *, offset: int = None) -> UnpackLenResult:
        offset = offset or 0
        total_read = 0
        results = []
        for child, nested in self.__sub_layouts:
            read, r = child.unpack_from_with_len(buffer, offset=offset + total_read)
            if nested:
                results.append(r)
            else:
                results.extend(r)
            total_read += read
        return total_read, tuple(results)

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[Tuple]:
        raise NotImplementedError

    def _iter_unpack_stream(self, stream: BinaryIO) -> Iterable[Tuple]:
        raise NotImplementedError
