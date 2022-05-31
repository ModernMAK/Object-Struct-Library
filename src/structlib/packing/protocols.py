from __future__ import annotations

import sys
from abc import ABC
from typing import Union, Any, Protocol, Optional, TypeVar, TYPE_CHECKING

from structlib.buffer_tools import calculate_padding
from structlib.byteorder import ByteOrderLiteral, ByteOrder, resolve_byteorder, Endian
from structlib.utils import default_if_none

T = TypeVar("T")


def struct_definition(obj: Union[StructDef, Any]) -> StructDef:
    _def = obj.__struct_def__
    if _def is obj:
        return _def
    else:
        return struct_definition(_def)


def struct_complete(obj: Union[StructDef, Any]) -> bool:
    """
    Whether the struct is considered 'complete'
    This will be false if alignment, size, or definition are not known.
    :param obj:
    :return:
    """
    return obj.__struct_complete__


def align_of(obj: Union[StructDef, Any]) -> int:
    return obj.__struct_alignment__


def align_as(obj: Union[T, Any], value: Union[StructDef, int]) -> T:
    if isinstance(value, int):
        alignment = value
    else:
        alignment = align_of(value)
    return obj.__struct_align_as__(alignment)


def endian_of(obj: Union[T, Any]) -> ByteOrderLiteral:
    return obj.__struct_endian__


def padding_of(obj: Union[BaseStructDefABC, Any]) -> int:
    alignment = align_of(obj)
    native_size = native_size_of(obj)
    return calculate_padding(alignment, native_size)


def native_size_of(obj: Union[BaseStructDefABC, Any]):
    """
    Returns the native size (un-padded) of the type
    :param obj:
    :return int: Un-padded size of struct
    """
    return obj.__struct_native_size__


class StructDef(Protocol):
    __struct_def__: StructDef
    __struct_endian__: ByteOrderLiteral
    __struct_native_size__: int
    __struct_alignment__: int
    __struct_complete__: bool

    def __struct_align_as__(self: T, alignment: int) -> T:
        ...

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        ...


class StructDefABC(ABC):
    if TYPE_CHECKING:
        __struct_def__: StructDefABC
        __struct_endian__: ByteOrderLiteral
        __struct_native_size__: int
        __struct_alignment__: int
        __struct_complete__: bool

    def __struct_align_as__(self: T, alignment: int) -> T:
        raise NotImplementedError(self.__class__)

    def __struct_endian_as__(self: T, endian: ByteOrder) -> T:
        raise NotImplementedError(self.__class__)

    def __eq__(self, other):
        def inner_eq():  # Both cases want to check these; but
            return self.__struct_native_size__ == other.__struct_native_size__ and \
                   self.__struct_alignment__ == other.__struct_alignment__ and \
                   self.__struct_complete__ == other.__struct_complete__ and \
                   self.__struct_endian__ == other.__struct_endian__

        if isinstance(other, BaseStructDefABC):
            self_def = struct_definition(self)
            other_def = struct_definition(other)
            if self is self_def and other is other_def:
                return inner_eq()
            else:
                return self_def == other_def and inner_eq()
        else:
            return False


class BaseStructDefABC(StructDefABC):
    def __init__(self, size: Optional[int] = None, align: Optional[int] = None, _def=None, complete: Optional[bool] = None, endian: Optional[ByteOrder] = None):
        self.__struct_def__ = _def or self
        self.__struct_endian__ = resolve_byteorder(endian)
        self.__struct_native_size__ = size
        self.__struct_alignment__ = default_if_none(align, size)
        self.__struct_complete__ = default_if_none(complete, not any([self.__struct_native_size__ is None, self.__struct_alignment__ is None]))


def endian_as(obj: Union[T, Any], value: ByteOrder) -> T:
    if value is None:
        endian = sys.byteorder
    elif isinstance(value, Endian):
        endian = value
    elif isinstance(value, str):
        endian = value  # TODO raise error if not literal
    else:
        endian = endian_of(value)
    return obj.__struct_endian_as__(endian)


def size_of(obj: Union[BaseStructDefABC, Any]):
    return native_size_of(obj) + padding_of(obj)
