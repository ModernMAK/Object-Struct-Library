from __future__ import annotations

import sys
from abc import ABCMeta
from collections import OrderedDict
from io import BytesIO
from typing import Any, Union, TypeVar, Tuple, Optional, BinaryIO, Dict, TYPE_CHECKING, ClassVar, Type, ForwardRef, _type_check, _eval_type

from structlib.buffer_tools import write_data_to_buffer, write_data_to_stream, calculate_padding
from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.packing.protocols import struct_definition, struct_complete, align_of, endian_of, native_size_of, StructDefABC, size_of
from structlib.packing.structure import StructStructABC
from structlib.typing_ import WritableBuffer

T = TypeVar("T")


def struct2args(t: Union[DataTypeStructDefABC, DataclassStruct, Any]) -> Tuple[Any, ...]:
    if hasattr(t, "__struct_struct2args__"):
        return t.__struct_struct2args__()
    else:
        return t


def args2struct(t: Union[Type[DataTypeStructDefABC], Type[DataclassStruct]], *args) -> T:
    if hasattr(t, "__struct_args2struct__"):
        return t.__struct_args2struct__(*args)
    else:
        return args


def get_type_buffer(t: StructDefABC, data: Optional[bytes] = None) -> WritableBuffer:
    """
    Gets a buffer for the type specified; data is copied to the first len(data) bytes if specified.

    :param t: Class/Instance of struct to build a buffer for
    :param data: The data to fill the buffer with (if present).
    :return bytearray: An aligned buffer which can be written to.
    """
    size = size_of(t)
    buffer = bytearray(size)
    if data is not None:
        buffer[0:len(data)] = data
    return buffer


def _max_align_of(*types: Union[StructDefABC, StructDefABC]):
    alignments = []
    for _type in types:
        alignment = align_of(_type)
        if alignment is None:  # type is not complete!
            return None
        else:
            alignments.append(alignment)
    return max(alignments) if len(alignments) > 0 else None


def _combined_size(*types: Union[StructDefABC, StructDefABC]):
    size = 0
    for t in types:
        t_size = size_of(t) + calculate_padding(align_of(t), size)
        if t_size is None:
            return None  # type is not complete!
        else:
            size += t_size
    return size


class Struct(StructStructABC):
    def __init__(self, *types: Union[StructDefABC, StructDefABC], alignment: int = None, endian: ByteOrder):
        if alignment is None:
            alignment = _max_align_of(*types)
        size = _combined_size(*types)
        super(Struct, self).__init__(size, alignment, self, endian=endian)  # complete will autogen
        self._types = types

    def __struct_align_as__(self: T, alignment: int) -> T:
        return self.__class__(self._types, align_as=alignment, endian=endian_of(self))

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        return self.__class__(self._types, align_as=align_of(self), endian=endian)

    def pack(self, *args: Any) -> bytes:
        if struct_complete(self):
            return self._fixed_pack(*args)
        else:
            return self._var_pack(*args)

    def _fixed_pack(self, *args: Any) -> bytes:
        buffer = bytearray(size_of(self))
        written = 0
        for t, a in zip(self._types, args):
            if not isinstance(a, tuple):
                a = (a,)
            _def = struct_definition(t)
            written += _def.pack_buffer(buffer, *a, offset=written, origin=0)
        return buffer

    def _var_pack(self, *args: Any) -> bytes:
        alignment = align_of(self)
        with BytesIO() as stream:
            for t, a in zip(self._types, args):
                if not isinstance(a, tuple):
                    a = (a,)
                _def = struct_definition(t)
                _def.pack_stream(stream, *a, origin=0)
            # Pad type to alignment
            padding = calculate_padding(alignment, stream.tell())
            stream.write([0x00] * padding)
            stream.seek(0)
            return stream.read()

    def unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        return self.unpack_buffer(buffer)[1]

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int = 0, origin: int = 0) -> int:
        alignment = align_of(self)
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=alignment, offset=offset, origin=origin)

    def unpack_buffer(self, buffer: bytes, offset: int = 0, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        alignment = align_of(self)
        padding = calculate_padding(alignment, offset)
        for t in self._types:
            _def = struct_definition(t)
            read_part, read_item = _def.unpack_buffer(buffer, offset=offset + read + padding, origin=origin)
            read += read_part
            items.append(read_item)
        return read, tuple(items)

    def pack_stream(self, stream: BinaryIO, *args: Any, origin: int = 0) -> int:
        alignment = align_of(self)
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=alignment, origin=origin)

    def unpack_stream(self, stream: BinaryIO, origin: int = 0) -> Tuple[int, Tuple[Any, ...]]:
        items = []
        read = 0
        alignment = align_of(self)
        padding = calculate_padding(alignment, stream.tell() - origin)
        stream.seek(origin + padding)
        for t in self._types:
            _def = struct_definition(t)
            read_part, read_item = _def.unpack_stream(stream, origin)
            read += read_part
            items.append(read_item)
        return read, tuple(items)


# @runtime_checkable (TypeError: @runtime_checkable can be only applied to protocol classes, got <class 'structlib.protocols.proto.DataTypeStructDef'>)
class DataclassStruct(StructDefABC):
    def __struct_struct2args__(self) -> Tuple[Any, ...]:
        ...

    @classmethod
    def __struct_args2struct__(cls, *args: Any) -> T:
        ...

    def pack(self) -> bytes:
        ...

    @classmethod
    def unpack(cls, buffer: bytes) -> T:
        ...

    def pack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> int:
        ...

    @classmethod
    def unpack_buffer(cls, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        ...

    def pack_stream(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> int:
        ...

    @classmethod
    def unpack_stream(cls, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        ...


def eval_fwd_ref(self: ForwardRef, globalns, localns, recursive_guard=frozenset()):
    if self.__forward_arg__ in recursive_guard:
        return self
    if not self.__forward_evaluated__ or localns is not globalns:
        if globalns is None and localns is None:
            globalns = localns = {}
        elif globalns is None:
            globalns = localns
        elif localns is None:
            localns = globalns
        if self.__forward_module__ is not None:
            globalns = getattr(
                sys.modules.get(self.__forward_module__, None), '__dict__', globalns
            )
        type_or_obj = eval(self.__forward_code__, globalns, localns)
        try:
            type_ = _type_check(
                type_or_obj,
                "Forward references must evaluate to types.",
                is_argument=self.__forward_is_argument__,
            )
            self.__forward_value__ = _eval_type(
                type_, globalns, localns, recursive_guard | {self.__forward_arg__}
            )
            self.__forward_evaluated__ = True
        except TypeError:
            self.__forward_value__ = type_or_obj  # should be object
            self.__forward_evaluated__ = True
    return self.__forward_value__


def resolve_annotations(raw_annotations: Dict[str, Type[Any]], module_name: Optional[str]) -> Dict[str, Type[Any]]:
    """
    Partially taken from typing.get_type_hints.
    Resolve string or ForwardRef annotations into types OR objects if possible.
    """
    base_globals: Optional[Dict[str, Any]] = None
    if module_name:
        try:
            module = sys.modules[module_name]
        except KeyError:
            # happens occasionally, see https://github.com/samuelcolvin/pydantic/issues/2363
            pass
        else:
            base_globals = module.__dict__

    annotations = {}
    for name, value in raw_annotations.items():
        if isinstance(value, str):
            if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (3, 10, 1):
                value = ForwardRef(value, is_argument=False, is_class=True)
            else:
                value = ForwardRef(value, is_argument=False)
            try:
                value = eval_fwd_ref(value, base_globals, None)
            except NameError:
                # this is ok, it can be fixed with update_forward_refs
                pass
        # except TypeError:  # forwardref points to an object!
        #     ...
        annotations[name] = value
    return annotations


class DataTypeStructDefMetaclass(ABCMeta, type):
    if sys.version_info < (3, 5):  # 3.5 >= is ordered by design
        @classmethod
        def __prepare__(cls, name, bases):
            return OrderedDict()

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: Dict[str, Any], alignment: int = None, endian:ByteOrder=None):
        if not bases:
            return super().__new__(mcs, name, bases, attrs)  # Abstract Base Class; AutoStruct

        if "__struct_def__" not in attrs:
            type_hints = resolve_annotations(attrs.get("__annotations__", {}), attrs.get("__module__"))
            typed_attr = {name: typing for name, typing in type_hints.items() if hasattr(typing, "__struct_def__")}
            ordered_attr = [name for name in type_hints.keys() if name in typed_attr]
            ordered_structs = [type_hints[attr] for attr in typed_attr]
            attrs["__struct_def__"] = struct = Struct(*ordered_structs, alignment=alignment,endian=resolve_byteorder(endian))
            attrs["__struct_types__"] = typed_attr
            attrs["__struct_type_order__"] = tuple(ordered_attr)
            attrs["__struct_native_size__"] = native_size_of(struct)
            attrs["__struct_alignment__"] = align_of(struct)
            attrs["__struct_complete__"] = struct_complete(struct)
        return super().__new__(mcs, name, bases, attrs)


class DataTypeStructDefABC(StructDefABC, metaclass=DataTypeStructDefMetaclass):
    def __init__(self):
        pass  # Intentionally avoid calling super for TypeStructABC

    if TYPE_CHECKING:
        __struct_def__: ClassVar[StructDefABC] = Struct()
        __struct_types__: ClassVar[Dict[str, StructDefABC]] = {}
        __struct_type_order__: ClassVar[Tuple[str, ...]]

    def __struct_struct2args__(self) -> Tuple[Any, ...]:
        names = self.__struct_type_order__
        attrs = [struct2args(getattr(self, n)) for n in names]
        return tuple(attrs)

    @classmethod
    def __struct_args2struct__(cls, *args: Any) -> T:
        names = cls.__struct_type_order__
        types = cls.__struct_types__
        kwargs = {}
        for name, arg in zip(names, args):
            t = types[name]
            if not isinstance(arg, tuple):
                kwargs[name] = args2struct(t, arg)[0]  # Preserve non-tuple
            else:
                kwargs[name] = args2struct(t, *arg)  # Preserve tuple
        # TODO figure out a proper solution
        inst = cls.__new__(cls)
        for name, value in kwargs.items():
            setattr(inst, name, value)
        return inst

    def pack(self) -> bytes:
        args = struct2args(self)
        _def = struct_definition(self)
        return _def.pack(*args)

    @classmethod
    def unpack(cls: T, buffer: bytes) -> T:
        _def = struct_definition(cls)
        args = _def.unpack(buffer)
        inst = args2struct(cls, *args)
        return inst

    def pack_buffer(self, buffer: WritableBuffer, *, offset: int = 0, origin: int = 0) -> int:
        args = struct2args(self)
        _def = struct_definition(self)
        return _def.pack_buffer(buffer, *args, offset=offset, origin=origin)

    @classmethod
    def unpack_buffer(cls, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
        _def = struct_definition(cls)
        read, args = _def.unpack_buffer(buffer, offset=offset, origin=origin)
        inst = args2struct(cls, *args)
        return read, inst

    def pack_stream(self, stream: BinaryIO, *, origin: int = None) -> int:
        args = struct2args(self)
        _def = struct_definition(self)
        return _def.pack_stream(stream, *args, origin)

    @classmethod
    def unpack_stream(cls, stream: BinaryIO, *, origin: int = None) -> Tuple[int, T]:
        _def = struct_definition(cls)
        read, args = _def.unpack_stream(stream, origin=origin)
        inst = args2struct(cls, *args)
        return read, inst


#
#


if __name__ == "__main__":
    import integer


    class MyIdea(DataTypeStructDefABC):
        int8: integer.Int8
        int16: integer.Int16
        int32: integer.Int32
        int64: integer.Int64(byteorder="big")

        def __init__(self, *args):
            super().__init__()
            self.int8, self.int16, self.int32, self.int64 = args

        def __str__(self):
            return f"MyIdea(int8={self.int8}, int16={self.int16}, int32={self.int32}, int64={self.int64})"


    inst = MyIdea(0x11, 0x22, 0x33, 0x44)
    print(inst)
    data = inst.pack()
    print(data.hex(sep=" ", bytes_per_sep=1))
    copy = MyIdea.unpack(data)
    print(copy)
