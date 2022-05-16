from abc import ABC
from typing import Tuple, BinaryIO, Any

from structlib.protocols import SubStructLikeMixin, WritableBuffer, ReadableBuffer
from structlib.protocols_dir.arg import ArgLikeMixin
from structlib.protocols_dir.size import SizeLikeMixin
from structlib.protocols_dir.align import Alignable
from structlib.utils import write_data_to_buffer, read_data_from_buffer, write_data_to_stream, read_data_from_stream


class PrimitiveStructMixin(SubStructLikeMixin, SizeLikeMixin, ABC):
    def __init__(self, *, size: int, align_as: int, args: int = 1):
        SizeLikeMixin.__init__(self, size)
        Alignable.__init__(self, align_as=align_as, default_align=size)
        ArgLikeMixin.__init__(self, args)

    def __eq__(self, other) -> bool:
        return isinstance(other, PrimitiveStructMixin) and \
               SizeLikeMixin.__eq__(self, other) and \
               Alignable.__eq__(self, other) and \
               ArgLikeMixin.__eq__(self, other)

    def _pack(self, *args: Any) -> bytes:
        raise NotImplementedError

    def pack(self, *args: Any) -> bytes:
        self.assert_args(len(args))
        return self._pack(*args)

    def _unpack(self, buffer: bytes) -> Tuple[Any,...]:
        raise NotImplementedError

    def unpack(self, buffer:bytes) -> Tuple[Any,...]:
        self.assert_size(len(buffer))
        return self._unpack(buffer)

    def pack_buffer(self, buffer: WritableBuffer, *args: int, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=self._align_, offset=offset, origin=origin)

    def _unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[int, ...]]:
        read, data = read_data_from_buffer(buffer, data_size=self._size_, align_as=self._align_, offset=offset, origin=origin)
        return read, self.unpack(data)

    def pack_stream(self, stream: BinaryIO, *args: int, origin: int = None) -> int:
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=self._align_, origin=origin)

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, Tuple[int, ...]]:
        data_size = self._size_
        read_size, data = read_data_from_stream(stream, data_size, align_as=self._align_, origin=origin)
        # TODO check stream size
        return read_size, self.unpack(data)
