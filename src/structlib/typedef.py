from __future__ import annotations

from abc import abstractmethod
from copy import copy
from typing import (
    TypeVar,
    runtime_checkable,
    Protocol,
    Type,
    Union,
    _ProtocolMeta,
    _is_callable_members_only,
    _get_protocol_attrs,
)

from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.errors import PrettyNotImplementedError

T = TypeVar("T")


class AttrProtocolMeta(_ProtocolMeta):
    # the lack of __instancehook__.
    def __instancecheck__(cls, instance):
        # We need this method for situations where attributes are
        # assigned in __init__.
        if (
                not getattr(cls, "_is_protocol", False) or _is_callable_members_only(cls)
        ) and issubclass(instance.__class__, cls):
            return True
        if cls._is_protocol:
            if all(
                    hasattr(instance, attr) and
                    # All *methods* can be blocked by setting them to None.
                    (
                            not callable(getattr(cls, attr, None))
                            or getattr(instance, attr) is not None
                    )
                    for attr in _get_protocol_attrs(cls)
            ):
                return True
            else:
                return False


@runtime_checkable
class TypeDefAlignable(Protocol):

    @property
    def __typedef_alignment__(self) -> int:
        raise PrettyNotImplementedError(self, "__typedef_alignment__")

    @abstractmethod
    def __typedef_align_as__(self: T, alignment: int) -> T:
        raise PrettyNotImplementedError(self, self.__typedef_align_as__)


class TypeDefAlignableABC(TypeDefAlignable):
    def __init__(self, alignment: int):
        self.__typedef_alignment = alignment

    @property
    def __typedef_alignment__(self) -> int:
        return self.__typedef_alignment

    def __typedef_align_as__(self: T, alignment: int) -> T:
        if self.__typedef_alignment__ == alignment:
            return self
        else:
            inst = copy(self)
            inst.__typedef_alignment__ = alignment
            return inst


@runtime_checkable
class TypeDefSizable(Protocol, metaclass=AttrProtocolMeta):
    """
    The type defines a native_size
    """

    __typedef_native_size__: int


class TypeDefSizableABC(TypeDefSizable):
    def __init__(self, native_size: int):
        self.__typedef_native_size__ = native_size


@runtime_checkable
class TypeDefByteOrder(Protocol):
    @property
    def __typedef_byteorder__(self) -> ByteOrder:
        raise PrettyNotImplementedError(self, "__typedef_byteorder__")

    @abstractmethod
    def __typedef_byteorder_as__(self: T, byteorder: ByteOrder) -> T:
        raise PrettyNotImplementedError(self, "__typedef_byteorder_as__")


class TypeDefByteOrderABC(TypeDefByteOrder):
    def __init__(self, byteorder: ByteOrder):
        self.__typedef_byteorder = byteorder

    @property
    def __typedef_byteorder__(self) -> ByteOrder:
        return self.__typedef_byteorder

    def __typedef_byteorder_as__(self: T, byteorder: ByteOrder) -> T:
        if self.__typedef_byteorder__ == byteorder:
            return self
        else:
            inst = copy(self)
            inst.__typedef_byteorder__ = byteorder
            return inst


@runtime_checkable
class TypeDefAnnotated(Protocol, metaclass=AttrProtocolMeta):
    """
    The typedef represents a pythonic type
    """

    @property
    def __typedef_annotation__(self) -> Type:
        raise PrettyNotImplementedError(self, "__typedef_annotation__")


def annotation_of(typedef: TypeDefAnnotated) -> Type:
    return typedef.__typedef_annotation__


def native_size_of(typedef: TypeDefSizable):
    # TODO ~ FIX HACK
    native_size = typedef.__typedef_native_size__
    if isinstance(native_size, property):
        native_size = native_size.fget(typedef)
    return native_size


def align_of(typedef: TypeDefAlignable) -> int:
    # TODO ~ FIX HACK
    #   Somehow, property is returning the instance instead of the result of fget
    #       Maybe because of dataclass?
    alignment = typedef.__typedef_alignment__
    if isinstance(alignment, property):
        alignment = alignment.fget(typedef)
    return alignment


def align_as(typedef: T, alignment: Union[TypeDefAlignable, int]) -> T:
    if isinstance(alignment, TypeDefAlignable):
        alignment = align_of(alignment)
    return typedef.__typedef_align_as__(alignment)


class TypeDefSizableAndAlignable(TypeDefSizable, TypeDefAlignable, Protocol):
    ...


def padding_of(typedef: TypeDefSizableAndAlignable):
    alignment = align_of(typedef)
    native_size = native_size_of(typedef)
    return calculate_padding(alignment, native_size)


def size_of(typedef: TypeDefSizable):
    native_size = native_size_of(typedef)
    padding = 0
    if isinstance(typedef, TypeDefAlignable):
        alignment = align_of(typedef)
        padding = calculate_padding(alignment, native_size)
    return native_size + padding


def byteorder_of(typedef: TypeDefByteOrder) -> ByteOrder:
    return typedef.__typedef_byteorder__


def byteorder_as(typedef: T, byteorder: Union[TypeDefByteOrder, ByteOrder]) -> T:
    if byteorder is None:
        byteorder = (
            resolve_byteorder()
        )  # For consistent behaviour, we don't just return NativeEndian
    if isinstance(byteorder, TypeDefByteOrder):
        byteorder = byteorder_of(byteorder)
    return typedef.__typedef_byteorder_as__(byteorder)


def calculate_padding(alignment: int, size_or_offset: int) -> int:
    """
    Calculates the padding required to align a buffer to a boundary.

    This function works for both sizes and offsets.
    If using a size; the padding is the padding required to align the type to the end of it's next `over aligned` boundary (suffix padding).
    If using an offset; the padding required to align the type to the start of its next `over aligned` boundary (prefix padding).

    :param alignment: The alignment in bytes. Any multiple of this value is an alignment boundary.
    :param size_or_offset: The size/offset to calculate padding for.
    :return: The padding required in terms of bytes.
    """
    bytes_from_boundary = size_or_offset % alignment
    if bytes_from_boundary != 0:
        return alignment - bytes_from_boundary
    else:
        return 0
