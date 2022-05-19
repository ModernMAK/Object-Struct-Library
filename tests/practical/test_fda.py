# from __future__ import annotations
#
# from dataclasses import dataclass
# from typing import Iterable, Tuple, List, Optional
#
# from structlib.definitions.array import Array
# from structlib.definitions.floating import Float32 as Float32Def
# from structlib.definitions.integer import UInt8 as UInt8Def
# from structlib.definitions.structure import Struct
# from structlib.enums import Endian
#
# UInt8 = UInt8Def(byteorder=Endian.Little)
# Float32 = Float32Def(byteorder=Endian.Little)
# Position = Normal = Array(3, Float32)
# Uv = Array(2, Float32)
# BoneWeight = Struct(Array(3, Float32), Array(4, UInt8))
# Float3 = Tuple[float, float, float]
# Float2 = Tuple[float, float]
# Byte4 = Tuple[int, int, int, int]
#
#
#
# class VertexBuffer():
#     def __init__(self, v_count, v_size):
#         self.positions: List[Float3] = []# 12
#         self.normals: List[Float3] = [] # 12
#         self.tex_coords: List[Float2] = [] # 8
#         self.bone_weights: Optional[List[Tuple[Float3, Byte4]]] = None# 16
#         self._backing = self.generate_vertex_buffer_struct(v_count,v_size)
#
#     SIMPLE_BUFFER_LAYOUT = 12 + 12 + 8
#     BONE_BUFFER_LAYOUT = SIMPLE_BUFFER_LAYOUT + (12 + 4)
#
#     @classmethod
#     def generate_vertex_buffer_struct(cls, v_count, v_size) -> Struct:
#         if v_size == cls.BONE_BUFFER_LAYOUT:
#             return Struct(
#                 Array(v_count, Position),
#                 Array(v_count, BoneWeight),
#                 Array(v_count, Normal),
#                 Array(v_count, Uv),
#             )
#         elif v_size == cls.SIMPLE_BUFFER_LAYOUT:
#             return Struct(
#                 Array(v_count, Position),
#                 Array(v_count, Normal),
#                 Array(v_count, Uv),
#             )
#         else:
#             raise NotImplementedError("V_Size",v_size)
#
#     def
#
#
# @dataclass
# class FdaDataChunk(DataChunk):
#     CHUNK_ID = "DATA"
#     CHUNK_TYPE = ChunkType.Data
#     LAYOUT = VStruct("< v")
#     # size: int
#     data: bytes
#
#     @classmethod
#     def convert(cls, chunk: GenericDataChunk) -> FdaDataChunk:
#         # VERSIONED
#         assert chunk.header.version in [1], chunk.header.version
#
#         data = cls.LAYOUT.unpack(chunk.raw_bytes)[0]
#         assert len(data) == len(chunk.raw_bytes) - cls.LAYOUT.min_size
#         return FdaDataChunk(chunk.header, data)
#
#
# @dataclass
# class FdaChunk(AbstractChunk):
#     CHUNK_TYPE = ChunkType.Folder
#     CHUNK_ID = "FDA "
#     # chunks: List[AbstractChunk]
#
#     info: FdaInfoChunk
#     data: FdaDataChunk
#
#     @property
#     def chunks(self) -> Iterable[AbstractChunk]:
#         yield self.info
#         yield self.data
#
#     @classmethod
#     def convert(cls, chunk: FolderChunk) -> FdaChunk:
#         assert chunk.header.version in [1], chunk.header.version
#         converted = FdaChunkConverter.convert_many(chunk.chunks)
#         x = ChunkCollectionX.list2col(converted)
#         info = x.find(FdaInfoChunk)
#         data = x.find(FdaDataChunk)
#         assert len(converted) == len(chunk.chunks) and len(chunk.chunks) == 2
#         return FdaChunk(chunk.header, info, data)
#
#
# @dataclass
# class FdaChunky(RelicChunky):
#     SUPPORTED_VERSIONS = [ChunkyVersion.v0101]
#     fbif: FbifChunk
#     fda: FdaChunk
#
#     @property
#     def chunks(self) -> Iterable[AbstractChunk]:
#         yield self.fbif
#         yield self.fda
#
#     @classmethod
#     def convert(cls, chunky: GenericRelicChunky) -> FdaChunky:
#         # VERSIONED
#         assert chunky.header.version in cls.SUPPORTED_VERSIONS, chunky.header.version
#         converted = FdaChunkConverter.convert_many(chunky.chunks)
#         x = ChunkCollectionX.list2col(converted)
#         fbif = x.find(FbifChunk)
#         fda = x.find(FdaChunk)
#         assert len(converted) == len(chunky.chunks) and len(chunky.chunks) == 2
#         return FdaChunky(chunky.header, fbif, fda)
#
#
# def add_fda_chunk_converter(conv: ChunkConverterFactory):
#     conv.register(FbifChunk)
#     conv.register(FdaInfoChunk)
#     conv.register(FdaDataChunk)
#     conv.register(FdaChunk)
#
#
# def generate_fda_chunk_converter():
#     conv = ChunkConverterFactory()
#     add_fda_chunk_converter(conv)
#     return conv
#
#
# # Individual converters are used to allow differing Chunkies to substitute their own Chunks
# FdaChunkConverter = generate_fda_chunk_converter()
