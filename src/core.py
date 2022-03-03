from abc import ABC
from enum import Flag
from typing import Protocol, Tuple, Iterable, List, BinaryIO


class ObjStructLike(Protocol):
    def pack(self, *args) -> bytes:
        ...

    def pack_into(self, buffer, *args, offset: int = 0):
        ...

    def iter_unpack(self, buffer):
        ...

    def unpack(self, string):
        ...

    def unpack_from(self, buffer, offset=0):
        ...


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

    @property
    def format(self) -> str:
        raise NotImplementedError

    @property
    def size(self) -> int:
        """ The fixed size of the buffer """
        raise NotImplementedError

    @property
    def min_size(self) -> int:
        """ The minimum size of the buffer """
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

    def pack_into(self, buffer, *args, offset: int = 0) -> int:
        raise NotImplementedError

    def pack_stream(self, buffer:BinaryIO, *args) -> int:
        raise NotImplementedError

    def unpack(self, buffer) -> Tuple:  # known case of _struct.Struct.unpack
        """
        Return a tuple containing unpacked values.

        Unpack according to the format string Struct.format. The buffer's size
        in bytes must be Struct.size.

        See help(struct) for more on format strings.
        """
        raise NotImplementedError

    def unpack_from(self, buffer, offset: int = 0) -> Tuple:  # known case of _struct.Struct.unpack_from
        """
        Return a tuple containing unpacked values.

        Values are unpacked according to the format string Struct.format.

        The buffer's size in bytes, starting at position offset, must be
        at least Struct.size.

        See help(struct) for more on format strings.
        """
        raise NotImplementedError

    def var_unpack_from(self, buffer, offset:int = 0) -> Tuple[int,Tuple]:
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError

    def unpack_stream(self, buffer:BinaryIO) -> Tuple:
        raise NotImplementedError


class ObjStructField(ObjStruct, ABC):
    DEFAULT_CODE = None
    IS_VAR_SIZE = None
    IS_STANDARD_STRUCT = None


class NestedStruct(ObjStruct):
    def __init__(self, structures:List[ObjStruct] = None):
        self.__sub_layouts: List[ObjStruct] = structures or []
        self.__args = sum(s.args for s in self.__sub_layouts)
        self.__is_var = any(s.is_var_size for s in self.__sub_layouts)
        self.__standard = all(hasattr(s, "IS_STANDARD_STRUCT") and s.IS_STANDARD_STRUCT for s in self.__sub_layouts)
        if self.__is_var:
            self.__size = sum(s.min_size for s in self.__sub_layouts)
        else:
            self.__size = sum(s.size for s in self.__sub_layouts)

    @property
    def size(self) -> int:
        if self.__is_var:
            raise TypeError("Variable sized structures do not have a fixed size!")
        return self.__size

    @property
    def min_size(self) -> int:
        return self.__size

    @property
    def format(self) -> str:
        raise NotImplementedError  # TODO, how to handle format

    @property
    def is_var_size(self) -> bool:
        return self.__is_var

    @property
    def args(self) -> int:
        return self.__args

    def pack(self, *args) -> bytes:
        r = bytearray()
        arg_offset = 0
        for s in self.__sub_layouts:
            s_args = args[arg_offset:arg_offset + s.args]
            arg_offset += s.args
            s_r = s.pack(s_args)
            r.extend(s_r)
        return r

    def pack_into(self, buffer, *args, offset: int = 0) -> int:
        arg_offset = 0
        if isinstance(buffer,BinaryIO):
            # same as StructWrapper __pack_into, but optimized for this use-case
            return_to = buffer.tell()
            buffer.seek(offset)
            written = 0
            for s_layout in self.__sub_layouts:
                s_args = args[arg_offset:arg_offset + s_layout.args]
                arg_offset += s_layout.args
                written += s_layout.pack_stream(buffer,*s_args)
            buffer.seek(return_to)
            return written
        else:
            buffer_local_offset = 0
            for s_layout in self.__sub_layouts:
                s_args = args[arg_offset:arg_offset + s_layout.args]
                arg_offset += s_layout.args
                buffer_local_offset += s_layout.pack_into(buffer, offset + buffer_local_offset, *s_args)
            return buffer_local_offset  # after all writes, should be number of bytes written

    def pack_stream(self, buffer: BinaryIO, *args) -> int:
        written = 0
        arg_offset = 0
        for s_layout in self.__sub_layouts:
            s_args = args[arg_offset:arg_offset + s_layout.args]
            arg_offset += s_layout.args
            written += s_layout.pack_stream(buffer, *s_args)
        return written

    def var_unpack_from(self, buffer, offset:int = 0) -> Tuple[int,Tuple]:
        results = []
        if isinstance(buffer, BinaryIO):
            return_to = buffer.tell()
            buffer.seek(offset)
            start = buffer.tell()
            for s_layout in self.__sub_layouts:
                r = s_layout.unpack_stream(buffer)
                results.extend(r)
            end = buffer.tell()
            buffer.seek(return_to)
            return end-start, tuple(results)
        else:
            buffer_local_offset = 0
            for s_layout in self.__sub_layouts:
                read_offset, r = s_layout.var_unpack_from(buffer, offset+buffer_local_offset)
                buffer_local_offset += read_offset
                results.extend(r)
            return buffer_local_offset, tuple(results)

    def unpack(self, buffer) -> Tuple:
        if len(self.__sub_layouts) == 1:
            return self.__sub_layouts[0].unpack(buffer)
        elif self.__is_var:
            results = []
            if isinstance(buffer,BinaryIO):
                for s_layout in self.__sub_layouts:
                    r = s_layout.unpack_stream(buffer)
                    results.extend(r)
            else:
                buffer_local_offset = 0
                for s_layout in self.__sub_layouts:
                    read_offset, r = s_layout.var_unpack_from(buffer, buffer_local_offset)
                    buffer_local_offset += read_offset
                    results.extend(r)
            return tuple(results)
        else:
            results = []
            if isinstance(buffer,BinaryIO):
                for s_layout in self.__sub_layouts:
                    r = s_layout.unpack_stream(buffer)
                    results.extend(r)
            else:
                buffer_local_offset = 0
                for s_layout in self.__sub_layouts:
                    r = s_layout.unpack_from(buffer, buffer_local_offset)
                    results.extend(r)
            return tuple(results)

    def unpack_from(self, buffer, offset: int = 0) -> Tuple:
        if len(self.__sub_layouts) == 1:
            return self.__sub_layouts[0].unpack_from(buffer, offset)
        elif self.__is_var:
            raise NotImplementedError()  # TODO, need to specify an expected buffer size IFF var_size, else we could just use unpack_from
        else:
            results = []
            if isinstance(buffer,BinaryIO):
                return_to = buffer.tell()
                buffer.seek(offset)
                for s_layout in self.__sub_layouts:
                    r = s_layout.unpack_stream(buffer)
                    results.extend(r)
                buffer.seek(return_to)
            else:
                buffer_local_offset = 0
                for s_layout in self.__sub_layouts:
                    r = s_layout.unpack_from(buffer, buffer_local_offset+offset)
                    results.extend(r)
            return tuple(results)

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        buffer_offset = 0
        if isinstance(buffer,BinaryIO):
            while True:           # TODO add a has_data function
                yield self.unpack_stream(buffer)
        else:
            while buffer_offset < len(buffer):
                yield self.unpack_from(buffer,buffer_offset)


