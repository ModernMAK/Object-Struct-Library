import sys
from typing import Tuple, BinaryIO

from structlib.protocols import SizeLikeMixin, AlignLikeMixin, SubStructLikeMixin


class _Integer(SubStructLikeMixin, SizeLikeMixin, AlignLikeMixin):
    def __init__(self, reps: int = 1, *, args: int, size: int, align_as: int = None, byteorder: str = None, signed: bool):
        self.__reps = reps
        self.__size = size
        self.__align = align_as or size
        self.__byteorder = byteorder or sys.byteorder
        self.__signed = signed
        self.__args = args

    def _align_(self) -> int:
        return self.__align

    def _size_(self) -> int:
        return self.__size * self.__args

    def _args_(self) -> int:
        return self.__args

    def _reps_(self) -> int:
        return self.__reps

    def unpack(self, buffer: bytes) -> Tuple[int, ...]:
        if self._size_() != len(buffer):
            # TODO raise error
            raise NotImplementedError
        items = []
        for rep in range(self.__reps):
            item = []
            for arg in range(self.__args):
                offset = (rep * self.__args + arg)
                arg_item = int.from_bytes(buffer[offset * self.__size:(offset + 1) * self.__size], byteorder=self.__byteorder, signed=self.__signed)
                item.append(arg_item)
            if len(item) == 1:  # Special case; dont use tuple
                item = item[0]
            else:
                item = tuple(item)
            items.append(item)
        return tuple(*items)

    def pack(self, *args: int) -> bytes:
        if len(args) != self.__args:
            # TODO raise error
            raise NotImplementedError
        buffer = bytearray()
        for arg in args:
            b = arg.to_bytes(self.__size, self.__byteorder, signed=self.__signed)
            buffer.extend(b)
        return buffer

    def pack_buffer(self, buffer: bytes, *args: int, offset: int = 0) -> int:
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset + data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[int, ...]]:
        read_size = self.__size * self.__reps * self.__args
        if len(buffer) < read_size:
            # TODO raise error
            raise NotImplementedError
        data = buffer[offset:offset + read_size]
        return self.__size, self.unpack(data)

    def pack_stream(self, stream: BinaryIO, *args: int) -> int:
        data = self.pack(*args)
        return stream.write(data)

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple[int, ...]]:
        read_size = self.__size * self.__reps * self.__args
        # TODO check stream size
        data = stream.read(read_size)
        return read_size, self.unpack(data)


class IntegerDefinition(_Integer):  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    class Integer(_Integer):

        ...
        # def __init__(self, args: int = 1, *, align_as: int = None, byteorder: str = None, size: int, signed: bool):
        #     super().__init__(args=args, size=size, signed=signed, align=align_as, byteorder=byteorder)

    def __init__(self, size: int, signed: bool, args: int = 1, *, align_as: int = None, byteorder: str = None):
        if size < 1:
            raise NotImplementedError  # Todo raise an error
        if args < 1:
            raise NotImplementedError  # Todo raise an error
        super().__init__(reps=1, args=args, size=size, signed=signed, align_as=align_as, byteorder=byteorder)
        self.__size = size
        self.__signed = signed
        self.__args = args
        self.__align_as = align_as
        self.__byteorder = byteorder

    def __call__(self, reps: int = 1, *, align_as: int = None, byteorder: str = None) -> Integer:
        return self.Integer(reps=reps, args=self.__args, align_as=align_as or self.__align_as, byteorder=byteorder or self.__byteorder, size=self.__size, signed=self.__signed)

    def __str__(self):
        type_str = f"{'' if self.__signed else 'U-'}Int{self.__size * 8}"
        tuple_str = '' if self.__args == 1 else f"x{self.__args}"
        return f"{type_str}{tuple_str}"

    def __eq__(self, other):
        # TODO, check 'same class' or 'sub class'
        raise NotImplementedError


Int8 = IntegerDefinition(1, True)
Int16 = IntegerDefinition(2, True)
Int32 = IntegerDefinition(4, True)
Int64 = IntegerDefinition(8, True)

UInt8 = IntegerDefinition(1, False)
UInt16 = IntegerDefinition(2, False)
UInt32 = IntegerDefinition(4, False)
UInt64 = IntegerDefinition(8, False)

if __name__ == "__main__":
    AltInt8 = IntegerDefinition(1, True)
    print(Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, AltInt8)
    print(repr(Int8), "is", repr(AltInt8), ":", (Int8 is AltInt8))
    print(Int8, "==", AltInt8, ":", (Int8 == AltInt8))
