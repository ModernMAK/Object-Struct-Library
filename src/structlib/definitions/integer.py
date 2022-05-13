from typing import Tuple, BinaryIO

from structlib.errors import FixedBufferSizeError, ArgCountError
from structlib.helper import default_if_none, ByteOrder, resolve_byteorder, ByteOrderLiteral
from structlib.protocols import SizeLikeMixin, AlignLikeMixin, SubStructLikeMixin, ArgLikeMixin, WritableBuffer, ReadableBuffer
from structlib.utils import write_data_to_buffer, write_data_to_stream, read_data_from_stream, read_data_from_buffer


class _Integer(SubStructLikeMixin, SizeLikeMixin):
    def __init__(self, *, size: int, signed: bool, align_as: int = None, byteorder: ByteOrder = None):
        AlignLikeMixin.__init__(self, align_as=align_as, default_align=size)
        SizeLikeMixin.__init__(self, size=size)
        ArgLikeMixin.__init__(self, args=1)
        self._byteorder = resolve_byteorder(byteorder)
        self._signed = signed

    def __eq__(self, other) -> bool:
        if not isinstance(other,_Integer):
            return False
        else:
            return self._byteorder == other._byteorder and self._signed == other._signed and \
                AlignLikeMixin.__eq__(self, other) and \
                SizeLikeMixin.__eq__(self, other) and \
                ArgLikeMixin.__eq__(self, other)

    @property
    def byte_order(self) -> ByteOrderLiteral:
        return self._byteorder

    @property
    def signed(self) -> bool:
        return self._signed

    def unpack(self, buffer: bytes) -> Tuple[int, ...]:
        if self._size_ != len(buffer):
            raise FixedBufferSizeError(len(buffer), self._size_)
        result = int.from_bytes(buffer, byteorder=self._byteorder, signed=self._signed)
        return tuple([result])

    def pack(self, *args: int) -> bytes:
        if len(args) != self._args_():
            raise ArgCountError(len(args), self._args_())
        return args[0].to_bytes(self._size_, self._byteorder, signed=self._signed)

    def pack_buffer(self, buffer: WritableBuffer, *args: int, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=self._align_, offset=offset, origin=origin)

    def _unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[int, ...]]:
        read, data = read_data_from_buffer(buffer, data_size=self._size_, align_as=self._align_, offset=offset, origin=origin)
        return read, self.unpack(data)
        # read_size = self._size_
        # if len(buffer) - (offset + origin) < read_size:
        #     # TODO raise error
        #     raise NotImplementedError
        # data = buffer[origin + offset:origin + offset + read_size]
        # return self._size_, self.unpack(data)

    def pack_stream(self, stream: BinaryIO, *args: int, origin: int = None) -> int:
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=self._align_, origin=origin)

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, Tuple[int, ...]]:
        data_size = self._size_
        read_size, data = read_data_from_stream(stream, data_size, align_as=self._align_, origin=origin)
        # TODO check stream size
        return read_size, self.unpack(data)


class IntegerDefinition(_Integer):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    class Integer(_Integer):
        ...

    def __init__(self, size: int, signed: bool, *, align_as: int = None, byteorder: ByteOrder = None):
        if size < 1:
            raise NotImplementedError  # Todo raise an error
        super().__init__(size=size, signed=signed, align_as=align_as, byteorder=byteorder)

    def __call__(self, *, align_as: int = None, byteorder: ByteOrder = None) -> Integer:
        return self.Integer(align_as=default_if_none(align_as, self._align_), byteorder=default_if_none(byteorder, self.byte_order), size=self._size_, signed=self.signed)

    def __str__(self):
        return f"{'' if self._signed else 'U-'}Int{self._size_ * 8}"
        # type_str = f"{'' if self.__signed else 'U-'}Int{self.__size * 8}"
        # tuple_str = '' if self.__args == 1 else f"x{self.__args}"
        # return f"{type_str}{tuple_str}"



Int8 = IntegerDefinition(1, True)
Int16 = IntegerDefinition(2, True)
Int32 = IntegerDefinition(4, True)
Int64 = IntegerDefinition(8, True)
Int128 = IntegerDefinition(16, True)

UInt8 = IntegerDefinition(1, False)
UInt16 = IntegerDefinition(2, False)
UInt32 = IntegerDefinition(4, False)
UInt64 = IntegerDefinition(8, False)
UInt128 = IntegerDefinition(16, False)

if __name__ == "__main__":
    AltInt8 = IntegerDefinition(1, True)
    print(Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, AltInt8)
    print(repr(Int8), "is", repr(AltInt8), ":", (Int8 is AltInt8))
    print(Int8, "==", AltInt8, ":", (Int8 == AltInt8))
