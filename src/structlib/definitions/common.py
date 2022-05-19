from abc import ABC
from typing import BinaryIO, Any
from structlib.protocols import SizeLikeMixin, Alignable, ArgLikeMixin, UnpackResult
from structlib.protocols.pack import WritableBuffer, ReadableBuffer
from structlib.protocols_old import SubStructLikeMixin, write_data_to_buffer, read_data_from_buffer, write_data_to_stream, read_data_from_stream


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

    def _unpack(self, buffer: bytes) -> UnpackResult:
        raise NotImplementedError

    def unpack(self, buffer: bytes) -> UnpackResult:
        self.assert_size(len(buffer))
        return self._unpack(buffer)

    def pack_buffer(self, buffer: WritableBuffer, *args: int, offset: int = 0, origin: int = 0) -> int:
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=self._align_, offset=offset, origin=origin)

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> UnpackResult:
        read, data = read_data_from_buffer(buffer, data_size=self._size_, align_as=self._align_, offset=offset, origin=origin)
        return UnpackResult(read, *self._unpack(data).values)

    def pack_stream(self, stream: BinaryIO, *args: int, origin: int = None) -> int:
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=self._align_, origin=origin)

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> UnpackResult:
        data_size = self._size_
        read_size, data = read_data_from_stream(stream, data_size, align_as=self._align_, origin=origin)
        # TODO check stream size
        return UnpackResult(read_size, *self._unpack(data).values)
