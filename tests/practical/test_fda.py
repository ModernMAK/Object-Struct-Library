import pytest

from structlib.datastruct import datastruct
from structlib.typedefs.integer import IntegerDefinition
from structlib.typedefs.strings import PascalString
from structlib.typedefs.varlen import LengthPrefixedBytes

Int32 = IntegerDefinition(4, True, alignment=1, byteorder="little")
FdaString = PascalString(Int32, encoding="ascii", alignment=1)
FdaByteString = LengthPrefixedBytes(Int32, alignment=1)
_Int32Max = (2 ** 31) - 1


@datastruct
class FileBurnInfo:
    plugin: FdaString
    version: Int32
    name: FdaString
    timestamp: FdaString  # TODO replace with a Timestamp struct?


@datastruct
class InfoBlock:
    channels: Int32
    sample_size: Int32
    block_bitrate: Int32
    sample_rate: Int32
    begin_loop: Int32
    end_loop: Int32
    start_offset: Int32


@datastruct
class DataBlock:
    data: FdaByteString


@pytest.mark.parametrize("timestamp", ["April 11, 9:00:05 pm", "January 1, 7:32:54 am"])
@pytest.mark.parametrize("name", ["Horus", "Yarrick"])
@pytest.mark.parametrize("version", [1, 2, 4, 8, _Int32Max])
@pytest.mark.parametrize("plugin", ["Example Plugin", "FBIF Plugin", "Relic Game Tool FDA Plugin"])
class TestFBIF:

    @staticmethod
    def test_pack_symmetry(plugin, version, name, timestamp):
        args = (plugin, version, name, timestamp)
        inst = FileBurnInfo(*args)
        packed = inst.pack()
        unpacked = inst.unpack(packed)
        assert unpacked == inst

# # from __future__ import annotations
# #
# # from dataclasses import dataclass
# # from typing import Iterable, Tuple, List, Optional
# #
# # from structlib.definitions.array import Array
# # from structlib.definitions.floating import Float32 as Float32Def
# # from structlib.definitions.integer import UInt8 as UInt8Def
# # from structlib.definitions.structure import Struct
# # from structlib.enums import Endian
# #
# from copy import copy
# from dataclasses import dataclass
# from typing import Tuple, List, Optional, Type, Protocol
#
# import rng
# from structlib.byteorder import LittleEndian
# from structlib.protocols.packing import unpack
# from structlib.protocols.typedef import native_size_of, byteorder_as
# from structlib.typedefs.array import Array
# from structlib.typedefs.datastruct import DataStruct, redefine_datastruct, T
# from structlib.typedefs.floating import Float32
# from structlib.typedefs.integer import UInt8
# from structlib.utils import dataclass_str_format
#
# Byte = UInt8_LE = byteorder_as(UInt8, LittleEndian)
# Float = Float32_LE = byteorder_as(Float32, LittleEndian)
#
#
# class VertexWeight(DataStruct):
#     w0: Float
#     w1: Float
#     w2: Float
#
#     @property
#     def w3(self):
#         return 1 - (self.w0 + self.w1 + self.w2)
#
#     b0: Byte
#     b1: Byte
#     b2: Byte
#     b3: Byte
#
#     def get_pairs(self) -> Tuple[Tuple[float, int], ...]:
#         return (self.w0, self.b0), \
#                (self.w1, self.b1), \
#                (self.w2, self.b2), \
#                (self.w3, self.b3)
#
#     def __str__(self):
#         attrs = {}
#         for weight, bone in self.get_pairs():
#             if bone != 0xff:
#                 attrs[f"Bone[{bone}]"] = f"{weight:2.2%}"
#         return dataclass_str_format(self.__class__.__name__, attrs)
#
#     def __repr__(self):
#         return str(self)
#
#
# class FloatXY(DataStruct):
#     x: Float
#     y: Float
#
#
# class FloatXYZ(DataStruct):
#     x: Float
#     y: Float
#     z: Float
#
#
# Normal = Position = FloatXYZ
# TexCoord = FloatXY
#
# EXP_MIN_SIZE = native_size_of(Position) + native_size_of(Normal) + native_size_of(TexCoord)
# EXP_FULL_SIZE = EXP_MIN_SIZE + native_size_of(VertexWeight)
#
#
# class VertexBufferProtocol(Protocol):
#     positions: List[Position]
#     normals: List[Normal]
#     vertex_weights: Optional[List[VertexWeight]]
#     texcoords: Optional[List[TexCoord]]
#
#
# class MinimalVertexBuffer(DataStruct, VertexBufferProtocol):
#     positions: Array.Unsized(Position)
#     normals: Array.Unsized(Normal)
#
#     @property
#     def vertex_weights(self) -> None:
#         return None
#
#     texcoords: Array.Unsized(TexCoord)
#
#     @classmethod
#     def redefine(cls, vertex_count: int):
#         names = ["positions", "normals", "texcoords"]
#         annotations = copy(cls.__annotations__)
#         for name in names:
#             prev_arr: Array = annotations[name]
#             prev_type = prev_arr._backing
#             new_arr = Array(vertex_count, prev_type)
#             annotations[name] = new_arr
#         return redefine_datastruct(cls, annotations)
#
#
# class FullVertexBuffer(DataStruct, VertexBufferProtocol):
#     positions: Array.Unsized(Position)
#     vertex_weights: Array.Unsized(VertexWeight)
#     normals: Array.Unsized(Normal)
#     texcoords: Array.Unsized(TexCoord)
#
#     @classmethod
#     def redefine(cls: T, vertex_count: int) -> T:
#         names = ["positions", "vertex_weights", "normals", "texcoords"]
#         annotations = copy(cls.__annotations__)
#         for name in names:
#             prev_arr: Array = annotations[name]
#             prev_type = prev_arr._backing
#             new_arr = Array(vertex_count, prev_type)
#             annotations[name] = new_arr
#         return redefine_datastruct(cls, annotations)
#
#
# MIN_SIZE = native_size_of(MinimalVertexBuffer.redefine(1))
# FULL_SIZE = native_size_of(FullVertexBuffer.redefine(1))
#
