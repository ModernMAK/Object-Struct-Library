from typing import Tuple, Any, BinaryIO

from structlib.protocols import SubStructLike, SubStructLikeMixin


class Struct(SubStructLikeMixin):
    def __init__(self, *args: SubStructLike):
        self.sub_structs = args
        self.__args = sum(_._reps_() for _ in args)

    def pack(self, *args) -> bytes:
        buffer = bytearray()
        arg_offset = 0
        for sub_struct in self.sub_structs:
            reps = sub_struct._reps_()
            sub_args = args[arg_offset:arg_offset + reps]
            sub_data = sub_struct.pack(*sub_args)

            arg_offset += reps
            buffer.extend(sub_data)
        return buffer

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer)

    def _align_(self) -> int:
        raise NotImplementedError

    def _args_(self) -> int:
        raise NotImplementedError

    def _reps_(self) -> int:
        raise NotImplementedError

    def pack_buffer(self, buffer: bytes, *args, offset: int = 0) -> int:
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset + data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_buffer(buffer,offset=offset+read)
            read += read_part
            items.append(read_item)
        return read, tuple(items)

    def pack_stream(self, stream: BinaryIO, *args) -> int:
        data = self.pack(*args)
        return stream.write(data)

    def _unpack_stream(self, stream: BinaryIO) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_stream(stream)
            read += read_part
            items.append(read_item)
        return read, tuple(items)
