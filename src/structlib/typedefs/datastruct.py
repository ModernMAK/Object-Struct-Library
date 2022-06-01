# from __future__ import annotations
#
# import sys
# from abc import ABCMeta, ABC
# from collections import OrderedDict
# from io import BytesIO
# from typing import Any, Union, TypeVar, Tuple, Optional, BinaryIO, Dict, TYPE_CHECKING, ClassVar, Type, ForwardRef, _type_check, _eval_type, Protocol
#
# from structlib.buffer_tools import calculate_padding
# from structlib.errors import PrettyNotImplementedError
# from structlib.io.streamio import write
# from structlib.io.bufferio import write
# from structlib.byteorder import ByteOrder, resolve_byteorder
# from structlib.protocols.packing import StructPackable
#
# from structlib.protocols.typedef import TypeDefSizableAndAlignable, align_of, size_of, native_size_of, TypeDefAlignable
# from structlib.typedefs.structure import Struct
# from structlib.typing_ import WritableBuffer
#
# T = TypeVar("T")
#
#
# class TypedefDataclass(Protocol):
#     __typedef_dclass_struct_packable__:StructPackable
#
#     def __typedef_dclass2tuple__(self) -> Tuple[Any, ...]:
#         raise PrettyNotImplementedError(self,self.__typedef_dclass2tuple__)
#
#     @classmethod
#     def __typedef_tuple2dclass__(cls, *args: Any) -> T:
#         raise PrettyNotImplementedError(cls,cls.__typedef_tuple2dclass__)
#
#
#
# def eval_fwd_ref(self: ForwardRef, global_namespace, local_namespace, recursive_guard=frozenset()):
#     if self.__forward_arg__ in recursive_guard:
#         return self
#     if not self.__forward_evaluated__ or local_namespace is not global_namespace:
#         if global_namespace is None and local_namespace is None:
#             global_namespace = local_namespace = {}
#         elif global_namespace is None:
#             global_namespace = local_namespace
#         elif local_namespace is None:
#             local_namespace = global_namespace
#         if self.__forward_module__ is not None:
#             global_namespace = getattr(
#                 sys.modules.get(self.__forward_module__, None), '__dict__', global_namespace
#             )
#         type_or_obj = eval(self.__forward_code__, global_namespace, local_namespace)
#         try:
#             type_ = _type_check(
#                 type_or_obj,
#                 "Forward references must evaluate to types.",
#                 is_argument=self.__forward_is_argument__,
#             )
#             self.__forward_value__ = _eval_type(
#                 type_, global_namespace, local_namespace, recursive_guard | {self.__forward_arg__}
#             )
#             self.__forward_evaluated__ = True
#         except TypeError:
#             self.__forward_value__ = type_or_obj  # should be object
#             self.__forward_evaluated__ = True
#     return self.__forward_value__
#
#
# def resolve_annotations(raw_annotations: Dict[str, Type[Any]], module_name: Optional[str]) -> Dict[str, Type[Any]]:
#     """
#     Partially taken from typing.get_type_hints.
#     Resolve string or ForwardRef annotations into types OR objects if possible.
#     """
#     base_globals: Optional[Dict[str, Any]] = None
#     if module_name:
#         try:
#             module = sys.modules[module_name]
#         except KeyError:
#             # happens occasionally, see https://github.com/samuelcolvin/pydantic/issues/2363
#             pass
#         else:
#             base_globals = module.__dict__
#
#     annotations = {}
#     for name, value in raw_annotations.items():
#         if isinstance(value, str):
#             if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (3, 10, 1):
#                 value = ForwardRef(value, is_argument=False, is_class=True)
#             else:
#                 value = ForwardRef(value, is_argument=False)
#             try:
#                 value = eval_fwd_ref(value, base_globals, None)
#             except NameError:
#                 # this is ok, it can be fixed with update_forward_refs
#                 pass
#         annotations[name] = value
#     return annotations
#
#
# class TypeDefDataclassMetaclass(ABCMeta, type):
#     if sys.version_info < (3, 5):  # 3.5 >= is ordered by design
#         @classmethod
#         def __prepare__(cls, name, bases):
#             return OrderedDict()
#
#     def __new__(mcs, name: str, bases: tuple[type, ...], attrs: Dict[str, Any], alignment: int = None):
#         if not bases:
#             return super().__new__(mcs, name, bases, attrs)  # Abstract Base Class; AutoStruct
#
#         add_align_as_func = any((isinstance(basecls,TypeDefAlignable) for basecls in bases))
#
#         type_hints = resolve_annotations(attrs.get("__annotations__", {}), attrs.get("__module__"))
#         typed_attr = {name: typing for name, typing in type_hints.items()}
#         ordered_attr = [name for name in type_hints.keys() if name in typed_attr]
#         ordered_structs = [type_hints[attr] for attr in typed_attr]
#         attrs["__typedef_dclass_struct_packable__"] = Struct(*ordered_structs, alignment=alignment)
#         attrs["__typedef_dclass_name2type_lookup__"] = typed_attr
#         attrs["__typedef_dclass_name_order__"] = tuple(ordered_attr)
#
#         attrs["__typedef_native_size__"] = property(lambda self:native_size_of(self.__typedef_dclass_struct_packable__))
#         attrs["__typedef_alignment__"] = property(lambda self:native_size_of(self.__typedef_dclass_struct_packable__))
#         return super().__new__(mcs, name, bases, attrs)
#
# class TypeDefDataclassABC(TypedefDataclass,metaclass=TypeDefDataclassMetaclass):
#     if TYPE_CHECKING:
#         __typedef_dclass_struct_packable__: Struct
#
#         __struct_types__: ClassVar[Dict[str, BaseStructDefABC]] = {}
#         __struct_type_order__: ClassVar[Tuple[str, ...]]
#
#
# class DataTypeStructDefABC(StructDefABC, ABC, metaclass=DataTypeStructDefMetaclass):
#     if TYPE_CHECKING:
#         __struct_def__: ClassVar[BaseStructDefABC] = Struct()
#         __struct_types__: ClassVar[Dict[str, BaseStructDefABC]] = {}
#         __struct_type_order__: ClassVar[Tuple[str, ...]]
#
#     def __struct_struct2args__(self) -> Tuple[Any, ...]:
#         names = self.__struct_type_order__
#         attrs = [struct2args(getattr(self, n)) for n in names]
#         return tuple(attrs)
#
#     @classmethod
#     def __struct_args2struct__(cls, *args: Any) -> T:
#         names = cls.__struct_type_order__
#         types = cls.__struct_types__
#         kwargs = {}
#         for name, arg in zip(names, args):
#             t = types[name]
#             if not isinstance(arg, tuple):
#                 kwargs[name] = args2struct(t, arg)[0]  # Preserve non-tuple
#             else:
#                 kwargs[name] = args2struct(t, *arg)  # Preserve tuple
#         # TODO figure out a proper solution
#         inst = cls.__new__(cls)
#         for name, value in kwargs.items():
#             setattr(inst, name, value)
#         return inst
#
#     def pack(self) -> bytes:
#         args = struct2args(self)
#         _def = struct_definition(self)
#         return _def.pack(*args)
#
#     @classmethod
#     def unpack(cls: T, buffer: bytes) -> T:
#         _def = struct_definition(cls)
#         args = _def.unpack(buffer)
#         inst = args2struct(cls, *args)
#         return inst
#
#     def pack_buffer(self, buffer: WritableBuffer, *, offset: int = 0, origin: int = 0) -> int:
#         args = struct2args(self)
#         _def = struct_definition(self)
#         return _def.pack_buffer(buffer, *args, offset=offset, origin=origin)
#
#     @classmethod
#     def unpack_buffer(cls, buffer: bytes, *, offset: int = 0, origin: int = 0) -> Tuple[int, T]:
#         _def = struct_definition(cls)
#         read, args = _def.unpack_buffer(buffer, offset=offset, origin=origin)
#         inst = args2struct(cls, *args)
#         return read, inst
#
#     def pack_stream(self, stream: BinaryIO, *, origin: int = None) -> int:
#         args = struct2args(self)
#         _def = struct_definition(self)
#         return _def.pack_stream(stream, *args, origin)
#
#     @classmethod
#     def unpack_stream(cls, stream: BinaryIO, *, origin: int = None) -> Tuple[int, T]:
#         _def = struct_definition(cls)
#         read, args = _def.unpack_stream(stream, origin=origin)
#         inst = args2struct(cls, *args)
#         return read, inst
