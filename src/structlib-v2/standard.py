from __future__ import annotations
from typing import Iterable, Tuple, Any

from structlib.byte_enums import FormatSize, Endian, Alignment
from structlib.struct import HybridStructHelper
from structlib.util import hybridmethod
from packing import pack_fixed_buffer, unpack_fixed_buffer



class ArbitraryStructHelper:
    def _pack(self, *args) -> bytes:
        raise NotImplementedError

    def _pack_aligned(self, offset: int, *args, origin: int = 0) -> bytes:
        raise NotImplementedError

    def _unpack(self, buffer) -> Tuple[Any, ...]:
        raise NotImplementedError

    def _unpack_aligned(self, buffer, offset: int, *, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError


class ArbitraryInt(HybridStructHelper):
    def __init__(self, args: int, size: int, signed: bool = True, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Standard):
        self.__signed = signed
        self.__endian = endian
        self.__format_size = format_size
        self.__alignment_size = size
        self.__alignment_type = alignment_type
        self.__is_variable_size = False
        self.__arguments = args
        self.__nested_arguments = 1
        self.__size = size

    @classmethod
    @property
    def default_instance(self) -> ArbitraryInt:
        raise NotImplementedError

    @hybridmethod
    @property
    def arguments(self) -> int:
        return self.default_instance.arguments

    @arguments.instance_method
    @property
    def arguments(self) -> int:
        return self.__arguments

    @hybridmethod
    @property
    def nested_arguments(self) -> int:
        return self.default_instance.nested_arguments

    @nested_arguments.instance_method
    @property
    def nested_arguments(self) -> int:
        return self.__nested_arguments

    @hybridmethod
    @property
    def fixed_size(self) -> int:
        return self.default_instance.fixed_size

    @fixed_size.instance_method
    @property
    def fixed_size(self) -> int:
        return self.__size * self.__arguments

    @hybridmethod
    @property
    def is_variable_size(self) -> bool:
        return self.default_instance.is_variable_size

    @is_variable_size.instance_method
    @property
    def is_variable_size(self) -> bool:
        return self.__is_variable_size

    @hybridmethod
    @property
    def alignment_size(self) -> int:
        return self.default_instance.alignment_size

    @alignment_size.instance_method
    @property
    def alignment_size(self) -> int:
        raise self.__alignment_size

    @hybridmethod
    @property
    def alignment_type(self) -> Alignment:
        return self.default_instance.alignment_type

    @alignment_type.instance_method
    @property
    def alignment_type(self) -> Alignment:
        return self.__alignment_type

    @hybridmethod
    @property
    def endian(self) -> Endian:
        return self.default_instance.endian

    @endian.instancemethod
    @property
    def endian(self) -> Endian:
        return self.__endian

    @hybridmethod
    @property
    def signed(self) -> bool:
        return self.default_instance.signed

    @signed.instancemethod
    @property
    def signed(self) -> bool:
        return self.__signed

    @hybridmethod
    @property
    def format_size(self) -> FormatSize:
        return self.default_instance.format_size

    @format_size.instance_method
    @property
    def format_size(self) -> FormatSize:
        return self.__format_size

    def _pack(self, *args: int) -> bytes:
        buffer = bytearray()
        for v in args:
            part = v.to_bytes(self.__size, self.__endian.value, signed=self.__signed)
            buffer.extend(part)
        return buffer

    def _pack_into(self, buffer, offset: int, *args: int, origin: int = 0) -> int:
        data = self._pack(*args)
        return pack_fixed_buffer(buffer, data, offset, self.__alignment_size, origin, self.__alignment_type)

    def _unpack(self, buffer, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        read_size, data = unpack_fixed_buffer(buffer, self.__size * self.__arguments, offset, self.__alignment_size, origin, self.__alignment_type)
        return read_size, tuple(int.from_bytes(data[_ * self.__size:(_ + 1) * self.__size], self.__endian.value, signed=self.__signed) for _ in range(self.__arguments))

    @hybridmethod
    def pack(self, *args) -> bytes:
        return self.default_instance.pack(*args)

    @pack.instance_method
    def pack(self, *args) -> bytes:
        return self._pack(*args)

    @hybridmethod
    def unpack(self, buffer) -> Tuple:
        return self.default_instance.unpack(buffer)

    @unpack.instance_method
    def unpack(self, buffer) -> Tuple[Any, ...]:
        raise self._unpack(buffer)

    @hybridmethod
    def pack_into(self, buffer, offset: int, *args) -> int:
        return self.default_instance.pack_into(buffer, offset, *args)

    @pack_into.instance_method
    def pack_into(self, buffer, offset: int, *args) -> int:
        return self._pack_into(buffer, offset, *args)

    @hybridmethod
    def unpack_from(self, buffer, offset: int) -> Tuple[Any, ...]:
        return self.default_instance.unpack_from(buffer, offset)

    @unpack_from.instance_method
    def unpack_from(self, buffer, offset: int) -> Tuple[Any, ...]:
        return self._unpack(buffer, offset)

    @hybridmethod
    def pack_stream(self, buffer, *args) -> bytes:
        return self.default_instance.pack_stream(buffer, *args)

    @pack_stream.instance_method
    def pack_stream(self, buffer, *args) -> bytes:
        raise NotImplementedError

    @hybridmethod
    def unpack_stream(self, buffer) -> Tuple[Any, ...]:
        return self.default_instance.unpack_stream(buffer)

    @unpack_stream.instance_method
    def unpack_stream(self, buffer) -> Tuple[Any, ...]:
        raise NotImplementedError

    @hybridmethod
    def iter_pack(self, buffer, *args: Tuple) -> int:
        return self.default_instance.iter_pack(buffer, *args)

    @iter_pack.instance_method
    def iter_pack(self, buffer, *args: Tuple) -> int:
        raise NotImplementedError

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        return self.default_instance.iter_unpack(buffer)

    @iter_unpack.instance_method
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError

    @hybridmethod
    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        return self.default_instance.nested_pack(buffer, offset, origin, *args)

    @nested_pack.instance_method
    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        data = self._pack(*args)
        return pack_fixed_buffer(buffer, data, offset, self.__alignment_size, origin, self.__alignment_type)

    @hybridmethod
    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        return self.default_instance.nested_unpack(buffer, offset, origin, *args)

    @nested_unpack.instance_method
    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        return self._unpack(buffer, offset, origin)


# UInt/Int 8, 16, 32, 64, also 128 because I know C# has 128 bit floating-point called 'decimal'

class Int8(ArbitraryInt):
    __BYTE_SIZE = 1
    __SIGNED = True

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(Int8, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> Int8:
        return cls()


class UInt8(ArbitraryInt):
    __BYTE_SIZE = 1
    __SIGNED = False

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(UInt8, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> UInt8:
        return cls()


class Int16(ArbitraryInt):
    __BYTE_SIZE = 2
    __SIGNED = True

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(Int16, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> Int16:
        return cls()


class UInt16(ArbitraryInt):
    __BYTE_SIZE = 2
    __SIGNED = False

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(UInt16, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> UInt16:
        return cls()


class Int32(ArbitraryInt):
    __BYTE_SIZE = 4
    __SIGNED = True

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(Int32, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> Int32:
        return cls()


class UInt32(ArbitraryInt):
    __BYTE_SIZE = 4
    __SIGNED = False

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(UInt32, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> UInt32:
        return cls()


class Int64(ArbitraryInt):
    __BYTE_SIZE = 8
    __SIGNED = True

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(Int64, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> Int64:
        return cls()


class UInt64(ArbitraryInt):
    __BYTE_SIZE = 8
    __SIGNED = False

    def __init__(self, args: int = 1, endian: Endian = Endian.Native, alignment_type: Alignment = Alignment.Native, format_size: FormatSize = FormatSize.Native):
        super(UInt64, self).__init__(args, self.__BYTE_SIZE, self.__SIGNED, endian, alignment_type, format_size)

    @classmethod
    @property
    def default_instance(cls) -> UInt64:
        return cls()
