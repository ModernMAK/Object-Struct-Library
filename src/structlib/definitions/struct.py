from io import BytesIO
from typing import Tuple, Any, BinaryIO

from structlib.protocols import SubStructLike, SubStructLikeMixin, AlignLikeMixin, ArgLikeMixin
from structlib.utils import align_of


class Struct(SubStructLikeMixin):
    def __init__(self, *args: SubStructLike, align_as: int = None):
        if not align_as:
            align_as = max((align_of(sub) for sub in args))
        AlignLikeMixin.__init__(self, align_as=align_as)
        ArgLikeMixin.__init__(self, args=len(args))
        self.sub_structs = args

    def pack(self, *args) -> bytes:
        with BytesIO() as stream:
            for sub_struct, sub_args in zip(self.sub_structs, args):
                if isinstance(sub_args, (list, tuple)):
                    sub_struct.pack_stream(stream, *sub_args,origin=0) # None will use NOW as the origin
                else:
                    sub_struct.pack_stream(stream, sub_args,origin=0) # None will use NOW as the origin
            stream.seek(0)
            return stream.read()

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer)[1]

    def _args_(self) -> int:
        return len(self.sub_structs)

    def pack_buffer(self, buffer: bytes, *args, offset: int = 0) -> int:
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset + data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_buffer(buffer, offset=offset + read, origin=origin)
            read += read_part
            items.extend(read_item)
        return read, tuple(items)

    def pack_stream(self, stream: BinaryIO, *args) -> int:
        data = self.pack(*args)
        return stream.write(data)

    def _unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_stream(stream)
            read += read_part
            items.append(read_item)
        return read, tuple(items)
