# Using IEEE_754
import math
import sys
from typing import Tuple, List

from structlib.protocols import SizeLikeMixin, PackLikeMixin


# a = Struct( Int8, UInt8, Int32 )
# Struct( Float * 6, a, 2 * half, 2 * Float )
# grouped = struct.pack("6fbBi2h2f")
#


# Sign  |   Significand     |   Fraction
# 1         (N-f-1)         |
#
# def fix_order(buffer: bytearray, byteorder: str) -> bytearray:
#     if byteorder != "little":
#         buffer.reverse()
#     return buffer
#
# def gen_zero(sign: bool, size: int) -> bytearray:
#     buffer = bytearray([0x00] * size)
#     buffer[0] |= 0b10000000 if sign else 0x00  # sign flag
#     return buffer
#
# def gen_inf(sign: bool, size: int, exponent_bits: int) -> bytearray:
#     buffer = gen_zero(sign,size) # creates properly sized buffer with sign bit set
#     for bit in range(exponent_bits):
#         byte = bit // 8
#         byte_bit = bit % 8
#         buffer[byte] |= (1 << byte_bit)
#     return buffer
#
#
# def gen_nan(sign: bool, size: int, exponent_bits: int, signaling: bool = False) -> bytearray:
#     buffer = gen_inf(sign, size, exponent_bits) # same layout but fraction has
#     raise NotImplementedError
#
#
#
# # This is a pretty garbage algo; could use struct to optimize 16/32/64 BUT wierd one's (like 90-bit floats) would need this to work properly
# def float2bin(f: float, size: int, exponent_bits: int) -> bytearray:
#     bit_size = size * 8
#     significand_size = bit_size - exponent_bits - 1  #
#     sign = math.copysign(1,f) > 0 # preserves sign of -0/+0
#     if math.isinf(f):
#         return gen_inf(sign, size, exponent_bits)
#     elif math.isnan(f):
#         return gen_nan(sign, size, exponent_bits)
#     elif f == 0: # not close, but IS 0
#         return gen_zero(sign, size)
#     else:
#         f = abs(f)
#
#     whole = int(f)
#     whole_buffer = bin(whole).lstrip("-0b")
#     fraction = f - whole
#     # We are guaranteed to only allow this many bits
#     #   If the number is subnormal; this will contain an extra bit that is discarded
#     fraction_bits = significand_size - (len(whole_buffer) - 1)
#     fraction_buffer_list = ["0" for _ in range(fraction_bits)]
#     for i in range(len(fraction_buffer_list)):
#         fraction *= 2
#         if fraction > 1:
#             fraction -= 1
#             fraction_buffer_list[i] = "1"
#     fraction_buffer = "".join(fraction_buffer_list)
#     # we now have two binary strings (whole/fraction)
#     #   Now we want to 'normalize' the string so that there is a 1 infront of the
#
#     if len(whole_buffer) == 0:  # SUB-NORMAL; discard the last bit of fraction and use as significand buffer; set exponent to 0
#         exponent = 0
#         significand_buffer = fraction_buffer[:-1]
#     else:
#         exponent =
#         significand_buffer = whole_buffer[1:] + fraction_buffer
#
#
#     byte_buffer = gen_zero(sign,size)
#     if len(whole_buffer) == 0: # SUB-NORMAL; discard the last bit
#         bit_offset = 1 + exponent_bits
#         for bit_pos, bit_char in enumerate():
#             buffer[]
#
#
#
#


# if __name__ == "__main__":
#     float2bin(0, 2, 5)


# float (IEEE)
#   size in bytes
#   1 bit -> sign
#   exponent ->
#   mantissa ->

# class BinaryFloatConverter:
#     SIGN_FLAG = 0b10000000
#
#     def __init__(self, exponent_bits:int, bytes:int):
#         self.bytes = bytes
#         self.bits = bytes * 8
#         self.exponent_bits = exponent_bits
#         self.sign_bits = 1
#         self.fraction_bits = self.bits - exponent_bits - 1
#
#         # wierd tricks, but basically shift enough bits, then subtract to get proper mask
#         self.exp_bias = 0b1 << (self.exponent_bits - 1) - 1
#         self.exp_max = 0b1 << (self.exponent_bits - 1)
#         self.exp_min = 0b1 - self.exp_bias
#
#
#     def gen_zero(self,pos:bool) -> bytes:
#         b = [0x00] * self.bytes
#         if pos: # set pos flag
#             b[0] = self.SIGN_FLAG
#         return bytes(b)
#
#     @staticmethod
#     def set_flag(b:List[int],bit:int):
#         byte = bit // 8
#         local_bit = bit % 8
#         b[byte] |= 1 << local_bit
#
#     @classmethod
#     def fill_exp(cls, b:List[int],exponent_bits:int):
#         for i in range(exponent_bits):
#             global_bit = i + 1 # assume 0 is sign
#             cls.set_flag(b,global_bit)
#
#     def gen_inf(self,pos:bool) -> bytes:
#         b = [0x00] * self.bytes
#         if pos: # set pos flag
#             b[0] = self.SIGN_FLAG
#         self.fill_exp(b,self.exponent_bits)
#         return bytes(b)
#
#     def gen_nan(self,pos:bool) -> bytes:
#         b = [0x00] * self.bytes
#         if pos: # set pos flag
#             b[0] = self.SIGN_FLAG
#         self.fill_exp(b,self.exponent_bits)
#         # any bit can be set in the fraction, but we chose this one because...
#         # it sets nan as quiet on some architectures (x86)
#         self.set_flag(b, self.exponent_bits+1+1)
#         return bytes(b)
#
#     def parse(self, b:bytes) -> Tuple[bool,int,int]:
#         mutable = bytearray(b)
#         pos = mutable[0] & self.SIGN_FLAG
#         mutable[0] &= ~self.SIGN_FLAG
#         # exponent = mutable[]
#
#
#
#     @classmethod
#     def positive(cls, f:float) -> bool:
#         return math.copysign(1, f) == 1
#
#
#     def to_bytes(self, f: float, byteorder: str = sys.byteorder) -> bytes:
#         b = self._to_bytes(f)
#         sign_pos = self.positive(f)
#         if
#
#         pre_dec = bin(int(f))
#         post_dec = f-pre_dec
#         post_dec_int =
#
#
#
#
#
#     @classmethod
#     def from_bytes(cls, b: bytes, byteorder: str = sys.byteorder) -> float:
#
#     @staticmethod
#     def _to_bytes(f: float) -> bytes:
#
#     @staticmethod
#     def _from_bytes(b: bytes) -> float:
#
#
#     class Float16:
#         SIGN_BIT_OFFSET = 15
#         SIGN_MASK = (1 << SIGN_BIT_OFFSET)
#
#         EXP_BIT_OFFSET = 10
#         EXP_MASK = (0b11111 << EXP_BIT_OFFSET)
#
#         FRAC_BIT_OFFSET = 0
#         FRAC_MASK = (0b1111111111 << FRAC_BIT_OFFSET)
#
#         @staticmethod
#         def to_bytes(f:float, byteorder:str=sys.byteorder) -> bytes:
#
#
#
#         @staticmethod
#         def _to_bytes(f: float) -> bytes:
#
#
#         @staticmethod
#         def _from_bytes(b:bytes) -> float:


class _Float(SizeLikeMixin, PackLikeMixin):
    def __init__(self, *, args: int, size: int, align_as: int = None, byteorder: str = None, exponent_bits: int):
        self.__size = size
        self.__align = align_as or size
        self.__byteorder = byteorder or sys.byteorder
        self.__args = args
        self.__exponent_bits = exponent_bits

    @staticmethod
    def sign_bits() -> int:
        return 1

    def exponent_bits(self) -> int:
        return self.__exponent_bits

    def mantissa_bits(self) -> int:
        return self.__size * 8 - (1 + self.__exponent_bits)

    def _align_(self) -> int:
        return self.__align

    def _size_(self) -> int:
        return self.__size * self.__args

    def unpack(self, buffer: bytes) -> Tuple[float, ...]:
        if self._size_() != len(buffer):
            # TODO raise error
            raise NotImplementedError
        raise NotImplementedError

    def pack(self, *args: float) -> bytes:
        if len(args) != self.__args:
            # TODO raise error
            raise NotImplementedError
        raise NotImplementedError


class FloatDefinition(_Float):
    class Float(_Float):
        ...

    def __init__(self, size: int, exponent_bits: int):
        super().__init__(args=1, size=size, exponent_bits=exponent_bits)
        self.__size = size
        self.__exponent_bits = exponent_bits

    @property
    def __fraction_bits(self) -> int:
        """ The explicitly stored fraction bits """
        return self.__size * 8 - self.__exponent_bits - 1  # sign bit

    def __call__(self, args: int = 1, *, align_as: int = None, byteorder: str = None) -> Float:
        return self.Float(args=args, align_as=align_as, byteorder=byteorder, size=self.__size, exponent_bits=self.__exponent_bits)

    def __str__(self):
        return f"Float{self.__size * 8}"

    def __eq__(self, other):
        return self.__size == other.__size and self.__exponent_bits == other.__exponent_bits


# def define_float(size: int, exponent_bits:int) -> FloatDefinition:
#     # inclusive mantissa INCLUDES the leading bit before the decimal
#     #   Our algo expects mantissa to be exclusive
#     if size < 1:
#         ...  # Todo raise an error
#     return FloatDefinition(size=size, exponent_bits=exponent_bits)


Float16 = FloatDefinition(size=2, exponent_bits=5)
Float32 = FloatDefinition(size=4, exponent_bits=8)
Float64 = FloatDefinition(size=8, exponent_bits=11)
Float128 = FloatDefinition(size=16, exponent_bits=15)
Float256 = FloatDefinition(size=32, exponent_bits=19)
