from typing import Tuple

from structlib.protocols import PackAndSizeLike, PackLikeMixin, AlignLikeMixin


class _VarString(AlignLikeMixin, PackLikeMixin):
    def __init__(self, *, args: int, align_as: int = None, encoding: str = None, size_struct: PackAndSizeLike):
        self.__align = align_as or 1
        self.__encoding = encoding
        # self.__byteorder = byteorder or sys.byteorder
        # self.__signed = signed
        self.__args = args
        self.__size_struct = size_struct

    def _align_(self) -> int:
        return self.__align

    def unpack(self, buffer: bytes) -> Tuple[str, ...]:
        items = []
        buffer_off = 0
        buffer_size_step = self.__size_struct._size_()
        for _ in range(self.__args):
            b_size = self.__size_struct.unpack(buffer[buffer_off:buffer_off+buffer_size_step])[0]
            buffer_off += buffer_size_step
            b_str_bytes = buffer[buffer_off:buffer_off+b_size]
            buffer_off += buffer_size_step
            b_str = b_str_bytes.decode(self.__encoding)
            items.append(b_str)
        return tuple(*items)

    def pack(self, *args: str) -> bytes:
        if len(args) != self.__args:
            # TODO raise error
            raise NotImplementedError
        buffer = bytearray()
        for arg in args:
            b_str = arg.encode(self.__encoding)
            b_size = self.__size_struct.pack(b_str)

            buffer.extend(b_size)
            buffer.extend(b_str)
        return buffer


class VarStringDefinition:  # Inheriting Integer allows it to be used without specifying an instance; syntax sugar for std type
    class VarString(_VarString):
        ...
        # def __init__(self, args: int = 1, *, align_as: int = None, byteorder: str = None, size: int, signed: bool):
        #     super().__init__(args=args, size=size, signed=signed, align=align_as, byteorder=byteorder)

    def __init__(self, size_struct: PackAndSizeLike, encoding: str = None):
        self.__size_struct = size_struct
        self.__encoding = encoding

    def __call__(self, args: int = 1, *, align_as: int = None) -> VarString:
        return self.VarString(args=args, align_as=align_as, size_struct=self.__size_struct, encoding=self.__encoding)

    def __str__(self):
        return f"VarString ({self.__encoding})"

    def __eq__(self, other):
        # TODO, check 'same class' or 'sub class'
        return self.__size_struct == other.__size_struct and self.__encoding == other.__encoding

if __name__ == "__main__":
    ...