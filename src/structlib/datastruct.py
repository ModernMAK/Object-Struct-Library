import copy
import dataclasses
import sys
from functools import partial
from types import NoneType
from typing import Optional, Tuple, TYPE_CHECKING, List, Dict, Callable

from structlib.packing import Packable, T, PackReadable, PackWritable
from structlib.typedef import TypeDefAnnotated
from structlib.typedefs.structure import Struct


def _get_globals(klass):
    if klass.__module__ in sys.modules:
        module = sys.modules[klass.__module__]
        return module.__dict__
    else:
        return {}


#
def _create_func(name, arguments: List[str], body: List[str], rtype: Optional[str] = "", globals: Optional[Dict] = None,
                 locals=None):
    locals = locals or {}
    return_def = f" -> {rtype}" if rtype != "" else ""
    func_def = f"def {name} ({', '.join(arguments)}){return_def}:"
    body_def = "\n\t".join(body)
    full_def = f"{func_def}\n\t{body_def}"
    injectable_def = full_def.replace("\t", "\t\t")  # Need to be one level deeper
    INJECTOR_NAME = "inject"
    INJECTOR_ARGS = ",".join(locals.keys())
    injector_def = f"def {INJECTOR_NAME}({INJECTOR_ARGS}):\n\t{injectable_def}\n\treturn {name}"
    resultspace = {}

    # create the injector
    exec(injector_def, globals, resultspace)
    # Run the injector
    return resultspace[INJECTOR_NAME](**locals)


def _inject_func(klass, func_name, func):
    if hasattr(klass, func_name):
        raise TypeError(f"{klass} has already defines `{func_name}`!")
    func.__qualname__ = f"{klass.__qualname__}.{func_name}"
    setattr(klass, func_name, func)


# def _dstruct_add_init(klass):
#     if klass.__module__ in sys.modules:
#         globals = sys.modules[klass.__module__].__dict__
#     else:
#         globals = {}
#
#     annotations = klass.__annotations__ if hasattr(klass, "__annotations__") else {}
#     init_args = [name for name, type in annotations.items()]
#     init_args.insert(0, "self")
#     body = [f"self.{name}={name}" for name, type in annotations.items()]
#     init_func = _create_fn("__init__", init_args, body, globals=globals)
#     # init_func = _create_func("__init__", init_args, body,globals=globals)
#     # TODO: Fix qualname
#     setattr(klass, "__init__", init_func)


# We don't need a separate StructField; we use type annotations to define the struct;
#   This SHOULD allow full compatibility with dataclass.Field, because annotations are updated before fields get updated in dataclass

# class StructField(dataclasses.Field):


_datastruct_tuplify_name = "_datastruct_args"


def _datastruct_tuplify(dclass, globals: Optional[Dict] = None) -> Tuple[str, Callable]:
    globals = _get_globals(dclass) if globals is None else globals
    locals = {"Tuple": Tuple}
    NAME = _datastruct_tuplify_name  # "_datastruct_args"
    RTYPE = "Tuple"
    _self_arg = "self"
    ARGS = [_self_arg]
    _arg_parts = [f"self.{f.name}" for f in dataclasses.fields(dclass)]
    _result_line = f"return ({', '.join(_arg_parts)})"
    BODY = [_result_line]
    return NAME, _create_func(NAME, ARGS, BODY, RTYPE, globals=globals, locals=locals)


# DO NOT INJECT COMMON FUNCTIONS
#   I'd prefer to have the callstack preserved for debugging ~ This is complicated enough without hiding information.

class hybridmethod:
    def __init__(self, inst=None, klass=None, doc=None):
        self._instance = inst
        self._klass = klass
        self._doc = doc

    def __doc__(self):
        return self._doc

    def instance(self, func):
        self._instance = func

    def klass(self, func):
        self._klass = func

    def __get__(self, instance, owner):
        if instance is not None:
            return partial(self._instance, instance)
        else:
            return partial(self._klass, owner)

    # def __call__(self, *args, **kwargs):
    #     print("X")
    #     pass


class classproperty:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self._fget = fget
        self._fset = fset
        self._fdel = fdel
        self._doc = doc

    def __doc__(self):
        return self._doc

    def getter(self, func):
        self._fget = func

    def setter(self, func):
        self._fset = func

    def deleter(self, func):
        self._fdel = func

    def __get__(self, instance, owner):
        return self._fget(owner)

    def __set__(self, instance, value):
        return self._fset(instance,value)

    def __delete__(self, instance):
        return self._fdel(instance)

    # def __call__(self, *args, **kwargs):
    #     print("X")
    #     pass


class _DatastructPackable:
    @classmethod
    def apply(cls, klass):
        _inject_func(klass, *_datastruct_tuplify(klass))
        klass.pack = hybridmethod(cls.pack, cls.pack_cls)
        klass.pack_into = hybridmethod(cls.pack_into, cls.pack_into_cls)
        klass.unpack = classmethod(cls.unpack)
        klass.unpack_from = classmethod(cls.unpack_from)

        klass.__typedef_annotation__ = classproperty(cls.__typedef_annotation__)
        klass.__typedef_alignment__ = classproperty(cls.__typedef_alignment__)
        klass.__typedef_native_size__ = classproperty(cls.__typedef_native_size__)
        klass.__typedef_align_as__ = classmethod(cls.__typedef_align_as__)

    @staticmethod
    def pack(self, arg: NoneType = None):
        if arg is not None:
            raise NotImplementedError
        struct_args = getattr(self, _datastruct_tuplify_name)()
        return self.__class__._struct.pack(struct_args)

    @staticmethod
    def pack_cls(cls, arg: T):
        struct_args = getattr(arg, _datastruct_tuplify_name)()
        return cls._struct.pack(struct_args)

    @staticmethod
    def __typedef_annotation__(cls):
        return cls

    @staticmethod
    def __typedef_alignment__(cls):
        return cls._struct.__typedef_alignment__

    @staticmethod
    def __typedef_native_size__(cls):
        return cls._struct.__typedef_native_size__

    @staticmethod
    def unpack(cls, buffer: bytes) -> T:
        args = cls._struct.unpack(buffer)
        return cls(*args)

    @staticmethod
    def pack_into_cls(cls, writable: PackWritable, arg: T, *, offset: Optional[int] = None, origin: int = 0):
        struct_args = getattr(arg, _datastruct_tuplify_name)()
        return cls._struct.pack_into(writable, struct_args, offset=offset, origin=origin)

    @staticmethod
    def pack_into(self, writable: PackWritable, arg: NoneType = None, *, offset: Optional[int] = None, origin: int = 0):
        if arg is not None:
            raise NotImplementedError
        struct_args = getattr(self, _datastruct_tuplify_name)()
        return self._struct.pack_into(writable, struct_args, offset=offset, origin=origin)

    @staticmethod
    def unpack_from(
            cls, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        read, args = cls._struct.unpack_from(readable, offset=offset, origin=origin)
        return read, cls(*args)

    @staticmethod
    def __typedef_align_as__(cls, alignment):
        raise NotImplementedError("DataStruct does not support post-def alignment assignment!")




class _EnumstructPackable:
    @classmethod
    def apply(cls, klass):
        klass.pack = hybridmethod(cls.pack, cls.pack_cls)
        klass.pack_into = hybridmethod(cls.pack_into, cls.pack_into_cls)
        klass.unpack = classmethod(cls.unpack)
        klass.unpack_from = classmethod(cls.unpack_from)

        klass.__typedef_annotation__ = classproperty(cls.__typedef_annotation__)
        klass.__typedef_alignment__ = classproperty(cls.__typedef_alignment__)
        klass.__typedef_native_size__ = classproperty(cls.__typedef_native_size__)
        klass.__typedef_align_as__ = classmethod(cls.__typedef_align_as__)

    @staticmethod
    def pack(self, arg: NoneType = None):
        if arg is not None:
            raise NotImplementedError
        enum_arg = self.value
        return self.__class__._struct.pack(enum_arg)

    @staticmethod
    def pack_cls(cls, arg: T):
        enum_arg = arg.value
        return cls._struct.pack(enum_arg)

    @staticmethod
    def __typedef_annotation__(self):
        return self.__class__

    @staticmethod
    def __typedef_alignment__(self):
        return self._struct.__typedef_alignment__

    @staticmethod
    def __typedef_native_size__(self):
        return self._struct.__typedef_native_size__

    @staticmethod
    def unpack(cls, buffer: bytes) -> T:
        arg = cls._struct.unpack(buffer)
        return cls(arg)

    @staticmethod
    def pack_into_cls(cls, writable: PackWritable, arg: T, *, offset: Optional[int] = None, origin: int = 0):
        enum_arg = arg.value
        return cls._struct.pack_into(writable, enum_arg, offset=offset, origin=origin)

    @staticmethod
    def pack_into(self, writable: PackWritable, arg: NoneType = None, *, offset: Optional[int] = None, origin: int = 0):
        if arg is not None:
            raise NotImplementedError
        enum_arg = self.value
        return self._struct.pack_into(writable, enum_arg, offset=offset, origin=origin)

    @staticmethod
    def unpack_from(
            cls, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        read, arg = cls._struct.unpack_from(readable, offset=offset, origin=origin)
        return read, cls(arg)

    @staticmethod
    def __typedef_align_as__(cls, alignment):
        raise NotImplementedError("EnumStruct does not support post-def alignment assignment!")


def datastruct(cls=None, /, alignment: int = None, **dataclass_kwargs):
    def resolve_annotation(t):
        return t.__typedef_annotation__ if isinstance(t, TypeDefAnnotated) else t

    def construct_struct(types):
        return Struct(*types, alignment=alignment)

    def wrap(klass):
        _anno = klass._dstruct_annotations = (
            klass.__annotations__ if hasattr(klass, "__annotations__") else {}
        )
        _resolved = klass.__annotations__ = {
            name: resolve_annotation(type)
            for name, type in klass._dstruct_annotations.items()
        }
        klass = dataclasses.dataclass(klass, **dataclass_kwargs)
        klass._struct = construct_struct(
            [t for t in klass._dstruct_annotations.values()]
        )
        _DatastructPackable.apply(klass)
        # print(klass.__typedef_alignment__)
        return klass

    if cls is None:
        return wrap  # Called with datastruct(...) or @datastruct(...)
    else:
        return wrap(cls)  # Called with @datastruct


def enumstruct(cls=None, /, backing_type: Packable = None):
    def wrap(klass):
        if backing_type is None:
            raise NotImplementedError

        klass._struct = backing_type
        _EnumstructPackable.apply(klass)
        return klass

    if cls is None:
        return wrap
    else:
        return wrap(cls)
