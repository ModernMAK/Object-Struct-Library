from abc import ABC
from typing import Tuple, Protocol, Iterable, Any
from byte_enums import Endian, FormatSize, Alignment

# noinspection PyPropertyDefinition
from structlib.packing import calculate_padding
from structlib.util import hybridmethod


class StructDefLike(Protocol):
    @property
    def byte_size(self) -> int:
        ...

    @property
    def alignment_size(self) -> int:
        ...


class StructDefHelper(ABC):
    def __init__(self, byte_size: int, alignment_size: int = None):
        self._byte_size = byte_size
        self._alignment_size = alignment_size or 1

    @property
    def byte_size(self) -> int:
        return self._byte_size

    @property
    def alignment_size(self) -> int:
        return self._alignment_size

    def calculate_padding(self, offset: int, origin: int = 0) -> int:
        return calculate_padding(offset, self._alignment_size, origin)

class StructPackerLike(Protocol):
    def pack(self,*args) -> bytes:
        """
        Packs the structure in a bytes like
        :param args: The values to pack
        :return: The values packed as a bytes-like object
        """
        ...
    def pack_aligned(self,position:int,*args) -> bytes:

        ...
    def unpack(self,buffer) -> Tuple[Any,...]:
        ...

class StructLike(Protocol):
    @property
    def arguments(self) -> int:
        ...

    @property
    def nested_arguments(self) -> int:
        ...

    @property
    def fixed_size(self) -> int:
        ...

    @property
    def is_variable_size(self) -> bool:
        ...

    @property
    def alignment_size(self) -> int:
        ...

    @property
    def alignment_type(self) -> Alignment:
        ...

    @property
    def endian(self) -> Endian:
        ...

    @property
    def format_size(self) -> FormatSize:
        ...

    def pack(self, *args) -> bytes:
        ...

    def unpack(self, buffer) -> Tuple:
        ...

    def pack_into(self, buffer, offset: int, *args, origin: int = 0) -> int:
        ...

    def unpack_from(self, buffer, offset: int, origin: int = 0) -> Tuple:
        ...

    def pack_stream(self, buffer, *args) -> bytes:
        ...

    def unpack_stream(self, buffer) -> Tuple:
        ...

    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        ...

    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        ...


class InstanceStructHelper:
    @property
    def arguments(self) -> int:
        raise NotImplementedError

    @property
    def nested_arguments(self) -> int:
        raise NotImplementedError

    @property
    def fixed_size(self) -> int:
        raise NotImplementedError

    @property
    def is_variable_size(self) -> bool:
        raise NotImplementedError

    @property
    def alignment_size(self) -> int:
        raise NotImplementedError

    @property
    def alignment_type(self) -> Alignment:
        raise NotImplementedError

    @property
    def endian(self) -> Endian:
        raise NotImplementedError

    @property
    def format_size(self) -> FormatSize:
        raise NotImplementedError

    def pack(self, *args) -> bytes:
        raise NotImplementedError

    def unpack(self, buffer) -> Tuple:
        raise NotImplementedError

    def pack_into(self, buffer, offset: int, *args) -> bytes:
        raise NotImplementedError

    def unpack_from(self, buffer, offset: int) -> Tuple:
        raise NotImplementedError

    def pack_stream(self, buffer, *args) -> bytes:
        raise NotImplementedError

    def unpack_stream(self, buffer) -> Tuple:
        raise NotImplementedError

    def iter_pack(self, buffer, *args: Tuple) -> int:
        raise NotImplementedError

    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError

    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        raise NotImplementedError

    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError


class HybridStructHelper:
    @hybridmethod
    @property
    def arguments(self) -> int:
        raise NotImplementedError

    @arguments.instance_method
    @property
    def arguments(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def nested_arguments(self) -> int:
        raise NotImplementedError

    @nested_arguments.instance_method
    @property
    def nested_arguments(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def fixed_size(self) -> int:
        raise NotImplementedError

    @fixed_size.instance_method
    @property
    def fixed_size(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def is_variable_size(self) -> bool:
        raise NotImplementedError

    @is_variable_size.instance_method
    @property
    def is_variable_size(self) -> bool:
        raise NotImplementedError

    @hybridmethod
    @property
    def alignment_size(self) -> int:
        raise NotImplementedError

    @alignment_size.instance_method
    @property
    def alignment_size(self) -> int:
        raise NotImplementedError

    @hybridmethod
    @property
    def alignment_type(self) -> Alignment:
        raise NotImplementedError

    @alignment_type.instance_method
    @property
    def alignment_type(self) -> Alignment:
        raise NotImplementedError

    @hybridmethod
    @property
    def endian(self) -> Endian:
        raise NotImplementedError

    @endian.instancemethod
    @property
    def endian(self) -> Endian:
        raise NotImplementedError

    @hybridmethod
    @property
    def format_size(self) -> FormatSize:
        raise NotImplementedError

    @format_size.instance_method
    @property
    def format_size(self) -> FormatSize:
        raise NotImplementedError

    @hybridmethod
    def pack(self, *args) -> bytes:
        raise NotImplementedError

    @pack.instance_method
    def pack(self, *args) -> bytes:
        raise NotImplementedError

    @hybridmethod
    def unpack(self, buffer) -> Tuple:
        raise NotImplementedError

    @unpack.instance_method
    def unpack(self, buffer) -> Tuple:
        raise NotImplementedError

    @hybridmethod
    def pack_into(self, buffer, offset: int, *args) -> bytes:
        raise NotImplementedError

    @pack_into.instance_method
    def pack_into(self, buffer, offset: int, *args) -> bytes:
        raise NotImplementedError

    @hybridmethod
    def unpack_from(self, buffer, offset: int) -> Tuple:
        raise NotImplementedError

    @unpack_from.instance_method
    def unpack_from(self, buffer, offset: int) -> Tuple:
        raise NotImplementedError

    @hybridmethod
    def pack_stream(self, buffer, *args) -> bytes:
        raise NotImplementedError

    @pack_stream.instance_method
    def pack_stream(self, buffer, *args) -> bytes:
        raise NotImplementedError

    @hybridmethod
    def unpack_stream(self, buffer) -> Tuple:
        raise NotImplementedError

    @unpack_stream.instance_method
    def unpack_stream(self, buffer) -> Tuple:
        raise NotImplementedError

    @hybridmethod
    def iter_pack(self, buffer, *args: Tuple) -> int:
        raise NotImplementedError

    @iter_pack.instance_method
    def iter_pack(self, buffer, *args: Tuple) -> int:
        raise NotImplementedError

    @hybridmethod
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError

    @iter_unpack.instance_method
    def iter_unpack(self, buffer) -> Iterable[Tuple]:
        raise NotImplementedError

    @hybridmethod
    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        raise NotImplementedError

    @nested_pack.instance_method
    def nested_pack(self, buffer, offset: int, origin: int, *args) -> int:
        raise NotImplementedError

    @hybridmethod
    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError

    @nested_unpack.instance_method
    def nested_unpack(self, buffer, offset: int, origin: int, *args) -> Tuple[int, Tuple[Any, ...]]:
        raise NotImplementedError
