from structlib.byteorder import ByteOrder
from structlib.definitions.structure import T
from structlib.packing.protocols import align_of, endian_of, size_of
from structlib.packing.primitive import PrimitiveStructABC
from structlib.utils import default_if_none


class BooleanDefinition(PrimitiveStructABC):
    TRUE = 0x01
    FALSE = 0x00

    def __struct_align_as__(self: T, alignment: int) -> T:
        return self.__class__(alignment=alignment, endian=endian_of(self))

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        return self.__class__(endian=endian, alignment=align_of(self))

    def __init__(self, *, alignment: int = None, endian: ByteOrder = None):
        """
        Creates a 'class' used to pack/unpack booleans.

        :param alignment: The alignment for this type, since booleans are always 1-byte, the over-aligned buffer will always be this size.
        :param endian: The 'endian' of the boolean, since booleans are always 1-byte, this value serves no purpose outside of struct semantics.
        """
        SIZE = 1  # Boolean's are always 1 byte
        alignment = default_if_none(alignment, SIZE)
        super().__init__(SIZE, alignment, self, endian=endian)

    def __call__(self, *, alignment: int = None, endian: ByteOrder = None):
        return self.__class__(alignment=default_if_none(alignment, align_of(self)), endian=default_if_none(endian, endian_of(self)))

    def pack(self, arg: bool) -> bytes:
        buffer = bytearray(size_of(self))  # Create (over) aligned buffer
        buffer[0] = self.TRUE if arg else self.FALSE
        return buffer

    def unpack(self, buffer: bytes) -> bool:
        return False if buffer[0] == self.FALSE else True


Boolean = BooleanDefinition()
