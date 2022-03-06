from enum import Flag
from io import BytesIO
from typing import Tuple, Iterable, List, Union, Type, Optional

from .error import StructPackingError, StructOffsetBufferTooSmallError, StructBufferTooSmallError, StructNestedPackingError
from .types import UnpackResult, UnpackLenResult, BufferStream, BufferApiType, Buffer, BufferStreamTypes


class ByteLayoutFlag(Flag):
    # DOH, these aren't flags; since it's 4 values
    #   Also currently unused
    NativeEndian = 0b00
    NetworkEndian = 0b01
    LittleEndian = 0b10
    BigEndian = 0b11

    NativeSize = 0b000
    StandardSize = 0b100

    NativeAlignment = 0b0000
    NoAlignment = 0b1000


class StructObj:
    @property
    def fixed_size(self) -> int:
        """
        The fixed size of the buffer; the minimum number of bytes read.
        For non-variable-length structs, this is the total number of bytes read.
        For variable-length structs, this is the minimum number of bytes read.
        """
        raise NotImplementedError

    @property
    def args(self) -> int:
        """
        The number of arguments this struct expects.

        Avoid GOTCHAs, Tuples, lists, and other collections should always be considered as 1 arg for consistency.
        :return: A non-negative integer.
        """
        raise NotImplementedError

    @property
    def is_var_size(self) -> bool:
        """
        Whether this
        :return: True if the struct's size is variable, False otherwise.
        """
        raise NotImplementedError

    def pack(self, *args) -> bytes:
        """
        Packs arguments into their specified byte format.
        :param args: The data to be packed to bytes.
        :return: The byte representation of args.
        """
        raise NotImplementedError

    def pack_stream(self, buffer: BufferStream, *args) -> int:
        """
        Packs arguments into their specified byte format into a binary stream-like buffer.
        The buffer's position is expected to have advanced to allow sequential writes to behave as expected.
        :param buffer: The binary stream to write to.
        :param args: The data to be packed to bytes.
        :return: The byte representation of args.
        """
        raise NotImplementedError

    def pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        """
        Packs arguments into their specified byte format into a buffer.
        If the buffer is a binary stream, the stream's position is not altered.
        :param buffer: The buffer to write to.
        :param args: The data to be packed to bytes.
        :param offset: The offset from the start of the buffer to write to in the buffer, defaults to the current position for binary streams and 0 for byte buffers.
        :return: The byte representation of args.
        """
        raise NotImplementedError

    def unpack(self, buffer: Buffer) -> UnpackResult:
        """
        Unpacks arguments from their specified byte format.
        :return: A tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def unpack_with_len(self, buffer) -> UnpackLenResult:
        """
        Unpacks arguments from their specified byte format.
        :return: A tuple containing the number of bytes read, and a tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def unpack_stream(self, buffer: BufferStream) -> UnpackResult:
        """
        Unpacks arguments using their specified byte format from a binary stream-like buffer.
        The buffer's position is expected to have advanced to allow sequential reads to behave as expected.
        :param buffer: The binary stream to read from.
        :return: A tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def unpack_stream_with_len(self, buffer) -> UnpackLenResult:
        """
        Unpacks arguments using their specified byte format from a binary stream-like buffer.
        The buffer's position is expected to have advanced to allow sequential reads to behave as expected.
        :param buffer: The binary stream to read from.
        :return: A tuple containing the number of bytes read, and a tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def unpack_from(self, buffer, offset: int = None) -> UnpackResult:
        """
        Packs arguments using their specified byte format from a buffer.
        If the buffer is a binary stream, the stream's position is not altered.
        :param buffer: The buffer to read from.
        :param offset: The offset from the start of the buffer to write to in the buffer, defaults to the current position for binary streams and 0 for byte buffers.
        :return: A tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def unpack_from_with_len(self, buffer, offset: int = None) -> UnpackLenResult:
        """
        Packs arguments using their specified byte format from a buffer.
        If the buffer is a binary stream, the stream's position is not altered.
        :param buffer: The buffer to read from.
        :param offset: The offset from the start of the buffer to write to in the buffer, defaults to the current position for binary streams and 0 for byte buffers.
        :return: A tuple containing the number of bytes read, and a tuple of the unpacked arguments.
        """
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        """
        Unpacks the buffer repeatedly until no more data can be read.
        :param buffer: The buffer to read from.
        :return: A tuple of the unpacked arguments.
        """
        raise NotImplementedError


class StructObjHelper(StructObj):  # Mixin to simplify functionality for custom structs
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

    def _stream_too_small(self, stream: BufferStream, offset: int = None) -> bool:
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
        if isinstance(buffer, BufferStreamTypes):
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

    def _pack_into_stream(self, stream: BufferStream, *args, offset: int = None) -> int:
        raise NotImplementedError

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        raise NotImplementedError

    def pack_into(self, buffer: Buffer, *args, offset: int = None) -> int:
        # Repeat to have errors in proper places
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_into.__name__, self.args, len(*args))
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.pack_into.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._pack_into_stream(buffer, *args, offset=offset)
        else:
            return self._pack_into_buffer(buffer, *args, offset=offset)

    def _pack_stream(self, buffer: BufferStream, *args) -> int:
        raise NotImplementedError

    def pack_stream(self, buffer: BufferStream, *args) -> int:
        # Repeat to have errors in proper places
        if self._arg_count_mismatch(*args):
            raise StructPackingError(self.pack_stream.__name__, self.args, len(*args))
        return self._pack_stream(buffer, *args)

    def _unpack_buffer(self, buffer: BufferApiType) -> UnpackLenResult:
        raise NotImplementedError

    def _unpack_stream(self, stream: BufferStream) -> UnpackLenResult:
        raise NotImplementedError

    def unpack(self, buffer: Buffer) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_stream(buffer)[1]
        else:
            return self._unpack_buffer(buffer)[1]

    def unpack_with_len(self, buffer) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_with_len.__name__, self.fixed_size, self.is_var_size)
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_stream(buffer)
        else:
            return self._unpack_buffer(buffer)

    def unpack_stream(self, buffer: BufferStream) -> UnpackResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)[1]

    def unpack_stream_with_len(self, buffer: BufferStream) -> UnpackLenResult:
        # Repeat to have errors in proper places
        if self._too_small(buffer):
            raise StructBufferTooSmallError(self.unpack_stream_with_len.__name__, self.fixed_size, self.is_var_size)
        return self._unpack_stream(buffer)

    def _unpack_from_buffer(self, buffer: BufferApiType, *, offset: int = None) -> UnpackLenResult:
        raise NotImplementedError

    def _unpack_from_stream(self, stream: BufferStream, *, offset: int = None) -> UnpackLenResult:
        raise NotImplementedError

    def unpack_from(self, buffer: Buffer, *, offset: int = None) -> UnpackResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_from_stream(buffer, offset=offset)[1]
        else:
            return self._unpack_from_buffer(buffer, offset=offset)[1]

    def unpack_from_with_len(self, buffer, offset: int = 0) -> UnpackLenResult:
        if self._too_small(buffer, offset):
            raise StructOffsetBufferTooSmallError(self.unpack_from_with_len.__name__, self.fixed_size, offset, None, self.is_var_size)  # TODO, pass in buffer size
        if isinstance(buffer, BufferStreamTypes):
            return self._unpack_from_stream(buffer, offset=offset)
        else:
            return self._unpack_from_buffer(buffer, offset=offset)

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[UnpackResult]:
        raise NotImplementedError

    def _iter_unpack_stream(self, stream: BufferStream) -> Iterable[UnpackResult]:
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[UnpackResult]:
        if isinstance(buffer, BufferStreamTypes):
            return self._iter_unpack_stream(buffer)
        else:
            return self._iter_unpack_buffer(buffer)


class MultiStruct(StructObjHelper):
    def __init__(self, *structures: Union[StructObj, Type[StructObj]]):
        sub_layouts = structures or []
        self.__is_var_size = any(s.is_var_size for s in sub_layouts)
        self.__size = sum(s.fixed_size for s in sub_layouts)
        self.__args = sum(1 if isinstance(s, MultiStruct) else s.args for s in sub_layouts)
        self.__sub_layouts: List[Tuple[StructObj, bool]] = [(s, isinstance(s, MultiStruct)) for s in sub_layouts]

    @property
    def fixed_size(self) -> int:
        return self.__size

    @property
    def is_var_size(self) -> bool:
        return self.__is_var_size

    @classmethod
    def __get_args(cls, s: StructObj) -> int:
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
            if nested:
                if len(child_args) != 1:
                    raise StructNestedPackingError(self._pack_stream.__name__, child_args.__class__)
                else:
                    child_args = child_args[0]
            arg_off += arg_c
            written += child.pack_into(buffer, *child_args, offset=offset + written)
        return written

    def _pack_into_buffer(self, buffer: BufferApiType, *args, offset: int = None) -> int:
        return self._pack_into(buffer, *args, offset=offset)

    def _pack_into_stream(self, buffer: BufferStream, *args, offset: int = None) -> int:
        return self._pack_into(buffer, *args, offset=offset)

    def _pack_stream(self, buffer: BufferStream, *args) -> int:
        arg_off = 0
        written = 0
        for child, nested in self.__sub_layouts:
            arg_c = 1 if nested else child.args
            child_args = args[arg_off:arg_off + arg_c]
            if nested:
                if len(child_args) != 1:
                    raise StructNestedPackingError(self._pack_stream.__name__, child_args.__class__)
                else:
                    child_args = child_args[0]
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

    def _unpack_stream(self, stream: BufferStream) -> UnpackLenResult:
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

    def _unpack_from_stream(self, stream: BufferStream, *, offset: int = None) -> UnpackLenResult:
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

    def _iter_unpack_buffer(self, buffer: BufferApiType) -> Iterable[UnpackResult]:
        offset = 0
        while offset < len(buffer):
            read, r = self._unpack_from_buffer(buffer, offset=offset)
            offset += read
            yield r

    def _iter_unpack_stream(self, stream: BufferStream) -> Iterable[UnpackResult]:
        while True:
            check = stream.read(1)
            if len(check) == 0:
                break
            else:
                stream.seek(-1, 1)
            yield self._unpack_stream(stream)[1]
