# from abc import ABC
# from typing import List, Any, Tuple
#
# import structlib.packing
# from structlib.byteorder import ByteOrder, NativeEndian
# from structlib.packing import Packable
# from structlib.typedef import native_size_of, TypeDefAlignable, align_of
# from structlib.typedefs import integer, floating
# from structlib.typedefs.floating import FloatDefinition
# from structlib.typedefs.structure import Struct
# from tests import rng
# from tests.typedefs.common_tests import AlignmentTests, StructureTests, Sample2Bytes
# from tests.typedefs.util import classproperty
#
#
# class StructTests(AlignmentTests, StructureTests, ABC):
#     @classproperty
#     def NATIVE_SIZE(self) -> int:
#         return native_size_of(self.TYPEDEF)
#
#     @classproperty
#     def TYPEDEF(self):
#         raise NotImplementedError
#
#     @classproperty
#     def NATIVE_PACKABLE(self) -> List[Packable]:
#         return [self.TYPEDEF]
#
#     @classproperty
#     def BIG_PACKABLE(self) -> List[Packable]:
#         return []
#
#     @classproperty
#     def LITTLE_PACKABLE(self) -> List[Packable]:
#         return []
#
#     @classproperty
#     def NETWORK_PACKABLE(self) -> List[Packable]:
#         return []
#
#     @classproperty
#     def ALIGNABLE_TYPEDEFS(self) -> List[TypeDefAlignable]:
#         return [self.TYPEDEF]
#
#     @classproperty
#     def OFFSETS(self) -> List[int]:
#         return [0, 1, 2, 4, 8]  # Normal power sequence
#
#     @classproperty
#     def ALIGNMENTS(self) -> List[int]:
#         return [1, 2, 4, 8]  # 0 not acceptable alignment
#
#     @classproperty
#     def ORIGINS(self) -> List[int]:
#         return [0, 1, 2, 4, 8]
#
#     @classproperty
#     def SAMPLE_COUNT(self) -> int:
#         # Keep it low for faster; less comprehensive, tests
#         return 16
#
#     @classproperty
#     def SAMPLES(self) -> List[Any]:
#         raise NotImplementedError
#
#     @classproperty
#     def SEEDS(self) -> List[int]:
#         # Random seed (unique per sub-test) and fixed seed
#         return [hash(self.__name__), 5 * 23 * 2022]
#
#     @classproperty
#     def ALIGN(self) -> int:
#         return align_of(self.TYPEDEF)
#
#
# class TestStructInt8Int16Uint8(StructTests):
#     @classproperty
#     def SAMPLES(self) -> List[Tuple[int, int, int]]:
#         seeds = self.SEEDS
#         sample_count = self.SAMPLE_COUNT // len(seeds)
#         sample_count = 1 if sample_count < 1 else sample_count
#         bom = NativeEndian
#         results = []
#         for seed in seeds:
#             a, b, c = rng.generate_seeds(3, seed)
#             for seeded_tuple in zip(
#                 rng.generate_ints(sample_count, a, 8, True, bom),
#                 rng.generate_ints(sample_count, b, 16, True, bom),
#                 rng.generate_ints(sample_count, c, 8, False, bom),
#             ):
#                 results.append(seeded_tuple)
#         return results
#
#     @classproperty
#     def TYPEDEF(self):
#         return Struct(integer.Int8, integer.Int16, integer.UInt8)
#
#     @classmethod
#     def get_sample2bytes(cls, byteorder: ByteOrder, alignment: int) -> Sample2Bytes:
#         def s2b(v: Tuple[int, int, int]) -> bytes:
#             int8 = int.to_bytes(v[0], 1, NativeEndian, signed=True)
#             int16 = int.to_bytes(v[1], 2, NativeEndian, signed=True)
#             uint8 = int.to_bytes(v[2], 1, NativeEndian, signed=False)
#             buf = bytearray()
#             buf.extend(int8)
#             buf.append(0x00)
#             buf.extend(int16)
#             buf.extend(uint8)
#             buf.append(0x00)
#             return buf
#
#         return s2b
#
#
# class TestStructFloat16Float32Float64(StructTests):
#     @classproperty
#     def SAMPLES(self) -> List[Tuple[float, float, float]]:
#         seeds = self.SEEDS
#         sample_count = self.SAMPLE_COUNT // len(seeds)
#         sample_count = 1 if sample_count < 1 else sample_count
#         bom = NativeEndian
#         results = []
#         for seed in seeds:
#             a, b, c = rng.generate_seeds(3, seed)
#             for seeded_tuple in zip(
#                 rng.generate_floats(sample_count, a, 16, bom),
#                 rng.generate_floats(sample_count, b, 32, bom),
#                 rng.generate_floats(sample_count, c, 64, bom),
#             ):
#                 results.append(seeded_tuple)
#         return results
#
#     @classproperty
#     def TYPEDEF(self):
#         return Struct(floating.Float16, floating.Float32, floating.Float64)
#
#     @classmethod
#     def get_sample2bytes(cls, byteorder: ByteOrder, alignment: int) -> Sample2Bytes:
#         def s2b(v: Tuple[int, int, int]) -> bytes:
#             f16 = FloatDefinition.INTERNAL_STRUCTS[(16, "little")].pack(v[0])
#             f32 = FloatDefinition.INTERNAL_STRUCTS[(32, "little")].pack(v[1])
#             f64 = FloatDefinition.INTERNAL_STRUCTS[(64, "little")].pack(v[2])
#             buf = bytearray()
#             buf.extend(f16)
#             buf.extend([0x00, 0x00])
#             buf.extend(f32)
#             buf.extend(f64)
#             return buf
#
#         return s2b
