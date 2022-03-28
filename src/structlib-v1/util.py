from struct import Struct
from typing import Callable, Union, Iterable, Tuple

# https://stackoverflow.com/questions/28237955/same-name-for-classmethod-and-instancemethod#:~:text=Class%20and%20instance%20methods%20live,will%20win%20in%20that%20case.&text=This%20is%20explicitly%20documented%3A,f()%20).
# BY Martijn Pieters
from structlib.types import BufferStream, BufferApiType, Buffer, BufferStreamTypes, UnpackResult, UnpackLenResult


class hybridmethod:
    def __init__(self, fclass: Union[Callable, property], finstance: Union[Callable, property] = None, doc=None):
        self.class_method = fclass
        self.instance_method = finstance
        self.__doc__ = doc or fclass.__doc__
        # support use on abstract base classes
        self.__isabstractmethod__ = bool(
            getattr(fclass, '__isabstractmethod__', False)
        )

    def classmethod(self, fclass):
        return type(self)(fclass, self.instance_method, None)

    def instancemethod(self, finstance):
        return type(self)(self.class_method, finstance, self.__doc__)

    def __get__(self, instance, cls):
        if instance is None or self.instance_method is None:
            # either bound to the class, or no instance method available
            return self.class_method.__get__(cls, None)
        return self.instance_method.__get__(instance, cls)


def pack_into_stream(layout: Struct, buffer: BufferStream, *args, offset: int = 0) -> int:
    return_to = buffer.tell()
    buffer.seek(offset)
    result = layout.pack(*args)
    buffer.write(result)
    buffer.seek(return_to)
    return layout.size


def pack_into_buffer(layout: Struct, buffer: BufferApiType, *args, offset: int = 0) -> int:
    layout.pack_into(buffer, offset, *args)
    return layout.size


def pack_into(layout: Struct, buffer: Buffer, *args, offset: int = 0) -> int:
    if isinstance(buffer, BufferStreamTypes):
        return pack_into_stream(layout, buffer, *args, offset=offset)
    else:
        return pack_into_buffer(layout, buffer, *args, offset=offset)


def pack_stream(layout: Struct, buffer: BufferStream, *args) -> int:
    result = layout.pack(*args)
    return buffer.write(result)


def unpack_buffer(layout: Struct, buffer: BufferApiType) -> UnpackResult:
    return layout.unpack(buffer)


def unpack_stream(layout: Struct, buffer: BufferStream) -> UnpackResult:
    byte_buffer = buffer.read(layout.size)
    return layout.unpack(byte_buffer)


def unpack(layout: Struct, buffer: Buffer) -> UnpackResult:
    if isinstance(buffer, BufferStreamTypes):
        return unpack_stream(layout, buffer)
    else:
        return unpack_buffer(layout, buffer)


def unpack_buffer_with_len(layout: Struct, buffer: BufferApiType) -> UnpackLenResult:
    return layout.size, layout.unpack(buffer)


def unpack_stream_with_len(layout: Struct, buffer: BufferStream) -> UnpackLenResult:
    byte_buffer = buffer.read(layout.size)
    return layout.size, layout.unpack(byte_buffer)


def unpack_with_len(layout: Struct, buffer: Buffer) -> UnpackLenResult:
    if isinstance(buffer, BufferStreamTypes):
        return unpack_stream_with_len(layout, buffer)
    else:
        return unpack_buffer_with_len(layout, buffer)


def unpack_from_buffer(layout: Struct, buffer: BufferApiType, offset: int = 0) -> UnpackResult:
    return layout.unpack_from(buffer, offset)


def unpack_from_stream(layout: Struct, buffer: BufferStream, offset: int = 0) -> UnpackResult:
    return_to = buffer.tell()
    buffer.seek(offset)
    stream_buffer = buffer.read(layout.size)
    result = layout.unpack(stream_buffer)
    buffer.seek(return_to)
    return result


def unpack_from(layout: Struct, buffer: Buffer, offset: int = 0) -> UnpackResult:
    if isinstance(buffer, BufferStreamTypes):
        return unpack_from_stream(layout, buffer, offset=offset)
    else:
        return unpack_from_buffer(layout, buffer, offset=offset)


def unpack_from_buffer_with_len(layout: Struct, buffer: BufferApiType, offset: int = 0) -> UnpackLenResult:
    return layout.size, layout.unpack_from(buffer, offset)


def unpack_from_stream_with_len(layout: Struct, buffer: BufferStream, offset: int = 0) -> UnpackLenResult:
    return_to = buffer.tell()
    buffer.seek(offset)
    stream_buffer = buffer.read(layout.size)
    result = layout.unpack(stream_buffer)
    buffer.seek(return_to)
    return layout.size, result


def unpack_from_with_len(layout: Struct, buffer: Buffer, offset: int = 0) -> UnpackLenResult:
    if isinstance(buffer, BufferStreamTypes):
        return unpack_from_stream_with_len(layout, buffer, offset=offset)
    else:
        return unpack_from_buffer_with_len(layout, buffer, offset=offset)


def iter_unpack_stream(layout: Struct, buffer: Buffer) -> Iterable[Tuple]:
    if layout.size == 0:
        raise ValueError("Layout has no size?!")
    while True:
        stream_buffer = buffer.read(layout.size)
        if len(stream_buffer) == 0:
            break
        yield layout.unpack(stream_buffer)


def iter_unpack_buffer(layout: Struct, buffer: Buffer) -> Iterable[Tuple]:
    return layout.iter_unpack(buffer)


def iter_unpack(layout: Struct, buffer) -> Iterable[Tuple]:
    if isinstance(buffer, BufferStreamTypes):
        return iter_unpack_stream(layout, buffer)
    else:
        return iter_unpack_buffer(layout, buffer)


