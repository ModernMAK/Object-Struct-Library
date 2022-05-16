from __future__ import annotations

import dataclasses
from io import BytesIO
from typing import Tuple, Any, BinaryIO, TypeVar, Type
from structlib.helper import default_if_none
from structlib.protocols import SubStructLike, SubStructLikeMixin
from structlib.protocols_dir import ArgLikeMixin, Alignable
from structlib.utils import align_of


class Struct(SubStructLikeMixin):
    def __init__(self, *sub_structs: SubStructLike, align_as: int = None):
        if not align_as:
            align_as = max((align_of(sub) for sub in sub_structs))
        Alignable.__init__(self, align_as=align_as)
        ArgLikeMixin.__init__(self, args=len(sub_structs))
        # TODO perform cyclic structure check
        #   Unpack/Pack will eventually fail (unless an infinite-buffer/cyclic generator is used; in which case: stack-overflow)
        #   __eq__ will stack-overflow
        self.sub_structs = sub_structs

    def __str__(self):
        return f"Struct ({', '.join([str(_) for _ in self.sub_structs])})"

    def __eq__(self, other):
        if self is other:
            return True
        elif not isinstance(other, Struct):
            return False
        else:
            if self._align_ != other._align_ or self._args_() != other._args_():
                return False
            for s, o in zip(self.sub_structs, other.sub_structs):
                if s != o:
                    return False
            return True

    def __call__(self, *, align_as: int) -> Struct:
        return Struct(*self.sub_structs, align_as=align_as)

    def pack(self, *args) -> bytes:
        with BytesIO() as stream:
            for sub_struct, sub_args in zip(self.sub_structs, args):
                if isinstance(sub_args, (list, tuple)):
                    sub_struct.pack_stream(stream, *sub_args, origin=0)  # None will use NOW as the origin
                else:
                    sub_struct.pack_stream(stream, sub_args, origin=0)  # None will use NOW as the origin
            stream.seek(0)
            return stream.read()

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        return self._unpack_buffer(buffer)[1]

    def pack_buffer(self, buffer: bytes, *args, offset: int = 0) -> int:
        # TODO fix origin logic
        data = self.pack(*args)
        data_len = len(data)
        buffer[offset:offset + data_len] = data
        return data_len

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        # TODO fix origin logic
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_buffer(buffer, offset=offset + read, origin=origin)
            read += read_part
            items.extend(read_item)
        return read, tuple(items)

    def pack_stream(self, stream: BinaryIO, *args, origin: int = None) -> int:
        # TODO fix origin logic
        data = self.pack(*args)
        return stream.write(data)

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, Tuple[Any, ...]]:
        # TODO fix origin logic
        items = []
        read = 0
        origin = default_if_none(origin, stream.tell())
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct._unpack_stream(stream, origin)
            read += read_part
            items.append(read_item)
        return read, tuple(items)


T = TypeVar('T')


class StructDataclass(Struct):
    """Experimental"""

    def __init__(self, *sub_structs: SubStructLike, align_as: int = None, dclass: Type[T]):
        super().__init__(*sub_structs, align_as=align_as)
        self._dclass = dclass

    def pack(self, dclass: T):
        args = dataclasses.astuple(dclass)
        return super(StructDataclass, self).pack(*args)

    def unpack(self, buffer: bytes) -> T:
        return self._unpack_buffer(buffer)[1]

    def pack_buffer(self, buffer: bytes, dclass: T, offset: int = 0) -> int:
        args = dataclasses.astuple(dclass)
        return super(StructDataclass, self).pack_buffer(buffer, *args, offset=offset)

    def _unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        read, result = super(StructDataclass, self)._unpack_buffer(buffer, offset=offset, origin=origin)
        return read, self._dclass(*result)

    def pack_stream(self, stream: BinaryIO, dclass: T, origin: int = None) -> int:
        args = dataclasses.astuple(dclass)
        return super(StructDataclass, self).pack_stream(stream, *args, origin=origin)

    def _unpack_stream(self, stream: BinaryIO, origin: int = None) -> Tuple[int, T]:
        read, result = super(StructDataclass, self)._unpack_stream(stream, origin=origin)
        return read, self._dclass(*result)
