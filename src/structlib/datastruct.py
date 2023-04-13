import copy
import dataclasses
from dataclasses import _is_dataclass_instance
from typing import Optional, Tuple, TYPE_CHECKING

from structlib.packing import Packable, T, PackReadable, PackWritable
from structlib.typedef import TypeDefAnnotated
from structlib.typedefs.structure import Struct


#
# def _create_func(name, arguments: List[str], body: List[str], rtype: Optional[str] = "", globals: Optional[Dict] = None,
#                  locals=None):
#     # locals = locals or {}
#
#     return_def = f" -> {rtype}" if rtype != "" else ""
#     func_def = f"def {name} ({', '.join(arguments)}){return_def}:"
#     body_def = "\n\t".join(body)
#     full_def = f"{func_def}\n\t{body_def}"
#     injectable_def = full_def.replace("\t", "\t\t")  # Need to be one level deeper
#     injector = "inject"
#     injector_def = f"def {injector}():\n\t{injectable_def}\n\treturn {name}"
#     resultspace = {}
#
#     # create the injector
#     exec(injector_def, globals, resultspace)
#     # Run the injector
#     return resultspace[injector]()


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


def astuple(obj, *, tuple_factory=tuple):
    """Return the fields of a dataclass instance as a new tuple of field values.

    Example usage::

      @dataclass
      class C:
          x: int
          y: int

    c = C(1, 2)
    assert astuple(c) == (1, 2)

    If given, 'tuple_factory' will be used instead of built-in tuple.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts.
    """

    if not _is_dataclass_instance(obj):
        raise TypeError("astuple() should be called on dataclass instances")

    result = []
    for f in dataclasses.fields(obj):
        value = _astuple_inner(getattr(obj, f.name), tuple_factory)
        result.append(value)
    return tuple_factory(result)


def _astuple_inner(obj, tuple_factory):
    if isinstance(obj, tuple) and hasattr(obj, "_fields"):
        # obj is a namedtuple.  Recurse into it, but the returned
        # object is another namedtuple of the same type.  This is
        # similar to how other list- or tuple-derived classes are
        # treated (see below), but we just need to create them
        # differently because a namedtuple's __init__ needs to be
        # called differently (see bpo-34363).
        return type(obj)(*[_astuple_inner(v, tuple_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        # Assume we can create an object of this type by passing in a
        # generator (which is not true for namedtuples, handled
        # above).
        return type(obj)(_astuple_inner(v, tuple_factory) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)(
            (_astuple_inner(k, tuple_factory), _astuple_inner(v, tuple_factory))
            for k, v in obj.items()
        )
    else:
        return copy.deepcopy(obj)


class _DataclassPackableMixin(Packable):
    if TYPE_CHECKING:
        _struct: Packable = None

    @classmethod
    def apply(cls, klass):
        klass.pack = cls.pack
        klass.unpack = cls.unpack
        klass.pack_into = cls.pack_into
        klass.unpack_from = cls.unpack_from

        klass.__typedef_annotation__ = cls.__typedef_annotation__
        klass.__typedef_alignment__ = cls.__typedef_alignment__
        klass.__typedef_native_size__ = cls.__typedef_native_size__

    @property
    def __typedef_annotation__(self):
        return self.__class__

    @property
    def __typedef_alignment__(self):
        return self._struct.__typedef_alignment__

    @property
    def __typedef_native_size__(self):
        return self._struct.__typedef_native_size__

    def pack(cls, arg: Optional[T] = None) -> bytes:
        if isinstance(cls, type):  # class call
            struct_args = astuple(arg)
            return arg._struct.pack(struct_args)
        else:
            if arg is not None:
                raise NotImplementedError
            struct_args = astuple(cls)  # cls is self
            return cls._struct.pack(struct_args)

    def unpack(cls, buffer: bytes) -> T:
        args = cls._struct.unpack(buffer)
        return cls.__class__(*args)

    @classmethod
    def pack_into(
            cls,
            writable: PackWritable,
            arg: Optional[T] = None,
            *,
            offset: Optional[int] = None,
            origin: int = 0,
    ) -> int:
        if isinstance(cls, type):  # class call
            struct_args = astuple(arg)
            return arg._struct.pack_into(
                writable, struct_args, offset=offset, origin=origin
            )
        else:
            if arg is not None:
                raise NotImplementedError
            struct_args = astuple(cls)  # cls is self
            return cls._struct.pack_into(
                writable, struct_args, offset=offset, origin=origin
            )

    @classmethod
    def unpack_from(
            cls, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        return cls._struct.unpack_from(readable, offset=offset, origin=origin)


class _EnumstructPackableMixin(Packable):
    if TYPE_CHECKING:
        _struct: Packable = None

    @classmethod
    def apply(cls, klass):
        klass.pack = cls.pack
        klass.unpack = cls.unpack
        klass.pack_into = cls.pack_into
        klass.unpack_from = cls.unpack_from

        klass.__typedef_annotation__ = cls.__typedef_annotation__
        klass.__typedef_alignment__ = cls.__typedef_alignment__
        klass.__typedef_native_size__ = cls.__typedef_native_size__

    @property
    def __typedef_annotation__(self):
        return self.__class__

    @property
    def __typedef_alignment__(self):
        return self._struct.__typedef_alignment__

    @property
    def __typedef_native_size__(self):
        return self._struct.__typedef_native_size__

    def pack(cls, arg: Optional[T] = None) -> bytes:
        if isinstance(cls, type):  # class call
            return arg._struct.pack(arg)
        else:
            if arg is not None:
                raise NotImplementedError
            return cls._struct.pack(cls)

    def unpack(cls, buffer: bytes) -> T:
        args = cls._struct.unpack(buffer)
        return cls.__class__(args)

    @classmethod
    def pack_into(
            cls,
            writable: PackWritable,
            arg: Optional[T] = None,
            *,
            offset: Optional[int] = None,
            origin: int = 0,
    ) -> int:
        if isinstance(cls, type):  # class call
            return arg._struct.pack_into(
                writable, arg, offset=offset, origin=origin
            )
        else:
            if arg is not None:
                raise NotImplementedError
            return cls._struct.pack_into(
                writable, cls, offset=offset, origin=origin
            )

    @classmethod
    def unpack_from(
            cls, readable: PackReadable, *, offset: Optional[int] = None, origin: int = 0
    ) -> Tuple[int, T]:
        return cls._struct.unpack_from(readable, offset=offset, origin=origin)


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
        _DataclassPackableMixin.apply(klass)
        # print(klass.__typedef_alignment__)
        return klass

    if cls is None:
        return wrap  # Called with datastruct(...) or @datastruct(...)
    else:
        return wrap(cls)  # Called with @datastruct


def enumstruct(cls=None, /, backing_type: Packable=None):
    def wrap(klass):
        if backing_type is None:
            raise NotImplementedError

        klass._struct = backing_type
        _EnumstructPackableMixin.apply(klass)
        return klass

    if cls is None:
        return wrap
    else:
        return wrap(cls)
