import dataclasses
import sys
from types import NoneType
from typing import List, Optional, Dict, Type


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


def _dstruct_add_init(klass):
    if klass.__module__ in sys.modules:
        globals = sys.modules[klass.__module__].__dict__
    else:
        globals = {}

    annotations = klass.__annotations__ if hasattr(klass, "__annotations__") else {}
    init_args = [name for name, type in annotations.items()]
    init_args.insert(0, "self")
    body = [f"self.{name}={name}" for name, type in annotations.items()]
    init_func = _create_fn("__init__", init_args, body, globals=globals)
    # init_func = _create_func("__init__", init_args, body,globals=globals)
    # TODO: Fix qualname
    setattr(klass, "__init__", init_func)


@dataclasses.dataclass
class StructLike:
    annotation: Type
    byteorder: Optional["byteorder"] # Byte order will default to the system byte order if not specified
    alignment: Optional[int] # Alignment will default to the size of the fixed type OR 1 if the size is not fixed
    fixed_size: Optional[int] # Static size of the type; None if the type has a variable size



def datastruct(cls=None, /, **dataclass_kwargs):
    def resolve_annotation(t):
        return t.annotation if isinstance(t, StructLike) else t

    def construct_struct(types):
        return None


    def wrap(klass):
        _anno = klass._dstruct_annotations = klass.__annotations__ if hasattr(klass, "__annotations__") else {}
        _resolved = klass.__annotations__ = {name: resolve_annotation(type) for name, type in klass._dstruct_annotations.items()}
        klass = dataclasses.dataclass(klass, **dataclass_kwargs)
        klass._struct = construct_struct([t for t in klass._dstruct_annotations.values()])
        return klass


    if cls is None:
        return wrap  # Called with datastruct(...) or @datastruct(...)
    else:
        return wrap(cls)  # Called with @datastruct


if __name__ == "__main__":
    @datastruct
    class Test:
        a: StructLike(str) = ""
        b: StructLike(NoneType) = None
        c: StructLike(int) = 6


    r = Test()
    t = dataclasses.astuple(r)
    print(r)
    print(r.__annotations__)
    print(t)