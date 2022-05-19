from __future__ import annotations

import dataclasses
import sys
from collections import OrderedDict
from io import BytesIO
from typing import Any, BinaryIO, TypeVar, Type, Union, Dict, ClassVar, Tuple, ForwardRef, Optional, _eval_type, _type_check

from structlib.definitions.common import PrimitiveStructMixin
from structlib.protocols import Alignable, ArgLikeMixin, align_of, calculate_padding, WritableBuffer, UnpackResult, ReadableBuffer
from structlib.protocols.size import VarSizeLikeMixin, size_of, VarSizeError
from structlib.protocols_old import SubStructLike, SubStructLikeMixin, write_data_to_buffer, write_data_to_stream
from structlib.utils import default_if_none


class Struct(SubStructLikeMixin, VarSizeLikeMixin):
    def __init__(self, *sub_structs: SubStructLike, align_as: int = None):
        if not align_as:
            align_as = max((align_of(sub) for sub in sub_structs))
        Alignable.__init__(self, align_as=align_as)
        ArgLikeMixin.__init__(self, args=len(sub_structs))
        size = 0
        try:
            for sub in sub_structs:
                alignment = align_of(sub)
                size += calculate_padding(alignment, size)  # Align type
                size += size_of(sub)
                size += calculate_padding(alignment, size)  # Pad type
            # Padding of THIS struct
            size += calculate_padding(align_of(self), size)
        except (VarSizeError, AttributeError):
            size = None
        VarSizeLikeMixin.__init__(self, size=size)

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
            if not Alignable.__eq__(self, other) or not ArgLikeMixin.__eq__(self, other):
                return False
            for s, o in zip(self.sub_structs, other.sub_structs):
                if s != o:
                    return False
            return True

    def __call__(self, *, align_as: int) -> Struct:
        return Struct(*self.sub_structs, align_as=align_as)

    def pack(self, *args: Any) -> bytes:
        if self.is_fixed_size:
            return self._fixed_pack(*args)
        else:
            return self._var_pack(*args)

    def _fixed_pack(self, *args: Any) -> bytes:
        buffer = bytearray(size_of(self))
        written = 0
        for sub_struct, sub_args in zip(self.sub_structs, args):
            if not isinstance(sub_args, tuple):
                sub_args = (sub_args,)
            written += sub_struct.pack_buffer(buffer, *sub_args, offset=written)
        # Padding should be included in size
        # padding = calculate_padding(align_as=align_of(self),offset=written)
        # T/ODO alignmnet padding
        return buffer

    def _var_pack(self, *args: Any) -> bytes:
        with BytesIO() as stream:
            for sub_struct, sub_args in zip(self.sub_structs, args):
                if not isinstance(sub_args, tuple):
                    sub_args = (sub_args,)
                sub_struct.pack_stream(stream, *sub_args, origin=0)  # None will use NOW as the origin
                padding = calculate_padding(align_as=align_of(self), offset=stream.seek())
                stream.write([0x00] * padding)
            stream.seek(0)
            return stream.read()

    def unpack(self, buffer: bytes) -> UnpackResult:
        return self.unpack_buffer(buffer)

    def pack_buffer(self, buffer: WritableBuffer, *args: Any, offset: int = 0, origin: int = 0) -> int:
        # TODO fix origin logic
        data = self.pack(*args)
        return write_data_to_buffer(buffer, data, align_as=align_of(self), offset=offset, origin=origin)

    def unpack_buffer(self, buffer: bytes, *, offset: int = 0, origin: int = 0) -> UnpackResult:
        # TODO fix origin logic
        padding = calculate_padding(align_of(self), offset)
        items = []
        read = 0
        for sub_struct in self.sub_structs:
            part = sub_struct.unpack_buffer(buffer, offset=offset + padding + read, origin=origin)
            read += part.bytes_read
            # Handle cases where pr
            items.extend(part.values)
        return UnpackResult(read, *items)

    def pack_stream(self, stream: BinaryIO, *args, origin: int = None) -> int:
        # TODO fix origin logic
        data = self.pack(*args)
        return write_data_to_stream(stream, data, align_as=align_of(self), origin=origin)

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> UnpackResult:
        # TODO fix origin logic
        items = []
        read = 0
        origin = default_if_none(origin, stream.tell())
        padding = calculate_padding(align_of(self), stream.tell() - origin)
        stream.seek(origin + padding)
        for sub_struct in self.sub_structs:
            read_part, read_item = sub_struct.unpack_stream(stream, origin)
            read += read_part
            items.append(read_item)
        return UnpackResult(read, *items)


T = TypeVar('T')


class StructDataclass(Struct):
    """Experimental"""

    def __init__(self, *sub_structs: SubStructLike, align_as: int = None, dclass: Type[T]):
        super().__init__(*sub_structs, align_as=align_as)
        self._dclass = dclass

    def _handle_args(self, *args: Union[T, Any]):
        if len(args) == 1 and isinstance(args[0], self._dclass):
            return dataclasses.astuple(args[0])
        else:
            return args

    def pack(self, *args: Union[T, Any]):
        args = self._handle_args(*args)
        return super(StructDataclass, self).pack(*args)

    def unpack(self, buffer: ReadableBuffer) -> UnpackResult:
        return self.unpack_buffer(buffer)

    def pack_buffer(self, buffer: WritableBuffer, *args: Union[T, Any], offset: int = 0) -> int:
        args = self._handle_args(*args)
        return super(StructDataclass, self).pack_buffer(buffer, *args, offset=offset)

    def unpack_buffer(self, buffer: ReadableBuffer, *, offset: int = 0, origin: int = 0) -> UnpackResult:
        result = super(StructDataclass, self).unpack_buffer(buffer, offset=offset, origin=origin)
        return UnpackResult(result.bytes_read, self._dclass(*result))

    def pack_stream(self, stream: BinaryIO, *args: Union[T, Any], origin: int = None) -> int:
        args = self._handle_args(*args)
        return super(StructDataclass, self).pack_stream(stream, *args, origin=origin)

    def unpack_stream(self, stream: BinaryIO, origin: int = None) -> UnpackResult:
        result = super(StructDataclass, self).unpack_stream(stream, origin=origin)
        return UnpackResult(result.bytes_read, self._dclass(*result))


from typing import TYPE_CHECKING

STRUCT_LAYOUT = "__struct_layout__"
STRUCT_ATTR = "__struct_attr__"
STRUCT_ORDER = "__struct_order__"
STRUCT_2_TUPLE = ""


def is_struct(cls: Union[type, object]):
    if not isinstance(cls, type):  # struct instance
        cls = cls.__class__
    return hasattr(cls, STRUCT_LAYOUT) or issubclass(cls, Struct) \
           or issubclass(cls, PrimitiveStructMixin) or issubclass(cls, SubStructLikeMixin)  # TODO replace [PrimitiveStructMixin/SubStructLikeMixin] with better alternative


# stolen from pydantic; modified to allow fwd-ref to obj
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
    Resolve string or ForwardRef annotations into type objects if possible.
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


class AutoStructMetaclass(type):
    if sys.version_info < (3, 5):  # 3.5 >= is ordered by design
        @classmethod
        def __prepare__(cls, name, bases):
            return OrderedDict()

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: Dict[str, Any], align_as: int = None):
        if not bases:
            attrs[STRUCT_LAYOUT] = None
            attrs[STRUCT_ATTR] = None
            return super().__new__(mcs, name, bases, attrs)  # Abstract Base Class; AutoStruct

        if STRUCT_LAYOUT not in attrs:
            annotations = resolve_annotations(attrs.get("__annotations__", {}), attrs.get("__module__"))
            typed_attr = {name: typing for name, typing in annotations.items() if is_struct(typing)}
            ordered_attr = [name for name in annotations.keys() if name in typed_attr]
            ordered_structs = [annotations[attr] for attr in typed_attr]
            attrs[STRUCT_LAYOUT] = Struct(*ordered_structs, align_as=align_as)
            attrs[STRUCT_ATTR] = typed_attr
            attrs[STRUCT_ORDER] = tuple(ordered_attr)
        return super().__new__(mcs, name, bases, attrs)


def struct2tuple(self: Union[AutoStruct, Any]) -> Tuple[Any, ...]:
    if hasattr(self, STRUCT_ATTR):
        attr = self.__struct_attr__.keys()
        return tuple([struct2tuple(getattr(self, a)) for a in attr])
    else:
        return self


def tuple2struct(cls: Type[AutoStruct], *args: Any) -> Union[AutoStruct, Any]:
    if hasattr(cls, STRUCT_ATTR) and hasattr(cls, STRUCT_ORDER):
        attr = cls.__struct_attr__
        order = cls.__struct_order__
        inst = cls.__new__(cls)
        for name, arg in zip(order, args):
            typing = attr[name]
            try:
                as_tuple = tuple2struct(typing, *arg)
            except TypeError:
                as_tuple = tuple2struct(typing, arg)[0]
            setattr(inst, name, as_tuple)
        return inst
    else:
        return args


class AutoStruct(metaclass=AutoStructMetaclass):
    if TYPE_CHECKING:
        __struct_layout__: ClassVar[Struct] = Struct()
        __struct_attr__: ClassVar[Dict[str, type]] = {}
        __struct_order__: ClassVar[Tuple[str, ...]]

    def __struct2tuple__(self) -> Tuple[Any, ...]:
        return struct2tuple(self)  # I did this backwards; I know

    @classmethod
    def __tuple2struct__(cls, *args: Any) -> AutoStruct:
        return tuple2struct(cls, *args)  # I did this backwards; I know

    def pack(self) -> bytes:
        args = self.__struct2tuple__()
        return self.__struct_layout__.pack(*args)

    @classmethod
    def unpack(cls, buffer: bytes) -> Tuple[int, AutoStruct]:
        _ = cls.__struct_layout__.unpack(buffer)
        inst = cls.__tuple2struct__(*_.values)
        return _.bytes_read, inst

    def pack_buffer(self, buffer: WritableBuffer, *, offset: int = 0, origin: int = 0) -> int:
        args = self.__struct2tuple__()
        return self.__struct_layout__.pack_buffer(buffer, *args, offset=offset, origin=origin)

    @classmethod
    def unpack_buffer(cls, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, AutoStruct]:
        _ = cls.__struct_layout__.unpack_buffer(buffer, offset=offset, origin=origin)
        inst = cls.__tuple2struct__(*_.values)
        return _.bytes_read, inst

    def pack_stream(self, stream: BinaryIO, *, origin: int = None) -> int:
        args = self.__struct2tuple__()
        return self.__struct_layout__.pack_stream(stream, *args, origin)

    @classmethod
    def unpack_stream(cls, stream: BinaryIO, *, origin: int = None) -> Tuple[int, AutoStruct]:
        _ = cls.__struct_layout__.unpack_stream(stream, origin=origin)
        inst = cls.__tuple2struct__(*_.values)
        return _.bytes_read, inst


if __name__ == "__main__":
    import integer


    class MyIdea(AutoStruct):
        int8: integer.Int8
        int16: integer.Int16
        int32: integer.Int32
        int64: integer.Int64(byteorder="big")

        def __init__(self, *args):
            self.int8, self.int16, self.int32, self.int64 = args

        def __str__(self):
            return f"MyIdea(int8={self.int8}, int16={self.int16}, int8={self.int32}, int8={self.int64})"


    inst = MyIdea(0x11, 0x22, 0x33, 0x44)
    print(inst)
    data = inst.pack()
    print(data.hex(sep=" ", bytes_per_sep=1))
    copy = MyIdea.unpack(data)[1]
    print(copy)
