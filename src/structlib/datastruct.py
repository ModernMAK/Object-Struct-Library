import dataclasses
import sys
from types import NoneType
from typing import List, Optional, Dict, Type

from structlib.typedef import TypeDefAnnotated
from structlib.typedefs.structure import Struct


def _is_packable(inst_or_klass):
    return False


from dataclasses import _create_fn


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


@dataclasses.dataclass
class StructLike:
    annotation: Type
    byteorder: Optional[
        "byteorder"
    ]  # Byte order will default to the system byte order if not specified
    alignment: Optional[
        int
    ]  # Alignment will default to the size of the fixed type OR 1 if the size is not fixed
    fixed_size: Optional[
        int
    ]  # Static size of the type; None if the type has a variable size
    # def pack(self, v) -> bytes:
    #     raise NotImplementedError
    #
    # def unpack(self, ):


# We don't need a separate StructField; we use type annotations to define the struct;
#   This SHOULD allow full compatibility with dataclass.Field, because annotations are updated before fields get updated in dataclass

# class StructField(dataclasses.Field):


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
        return klass

    if cls is None:
        return wrap  # Called with datastruct(...) or @datastruct(...)
    else:
        return wrap(cls)  # Called with @datastruct


if __name__ == "__main__":
    from structlib.typedefs.integer import Int8
    from structlib.typedefs.strings import PascalString
    from structlib.typedefs.boolean import Boolean

    TestString = PascalString(Int8)  # Pascal string supporting up to 256 chars

    @datastruct(alignment=4)
    class Test:
        age: Int8 = 8
        male: Boolean = True
        name: TestString = "Bobby Tables"

    r = Test()
    t = dataclasses.astuple(r)
    u = dataclasses.asdict(r)
    print(r)
    print(r._dstruct_annotations)
    print(r.__annotations__)
    print(t)
    print(u)
    packed = r._struct.pack(t)
    print(packed)
