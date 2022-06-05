# from __future__ import annotations
# from datetime import datetime
#
# from structlib.protocols.typedef import TypeDefSizable, native_size_of
# from structlib.typedefs.datastruct import DataStruct
# from structlib.typedefs.integer import IntegerDefinition
# from structlib.typedefs.strings import PascalString
#
# Int32 = IntegerDefinition(4, True, alignment=1, byteorder="little")
# FbifString = PascalString(Int32, "ascii")
#
#
# class FbifChunkData(DataStruct):
#     plugin: FbifString
#     version: Int32
#     name: FbifString
#     timestamp: FbifString
#
#     @classmethod
#     def default(cls) -> bytes:
#         RELIC_LIKE_TIMESTAMP_FORMAT = "%B %d, %I:%M:%S %p"  # Not perfect due to leading 0's
#         PLUGIN = "https://github.com/ModernMAK/Relic-SGA-Archive-Tool"
#         VERSION = 0
#         NAME = "Marcus Kertesz"
#         TIME_STAMP = datetime.now().strftime(RELIC_LIKE_TIMESTAMP_FORMAT)
#         return FbifChunkData.__typedef_dclass_struct_packable__.struct_pack(PLUGIN, VERSION, NAME, TIME_STAMP)
#
#
# if __name__ == "__main__":
#     assert not isinstance(PascalString, TypeDefSizable)
#     # native_size_of(PascalString(Int32))
#     assert not isinstance(PascalString(Int32), TypeDefSizable)
#     data = FbifChunkData.default()
#     r = FbifChunkData.dclass_unpack(data)
#     print(r)
#     data2 = r.dclass_pack()
#     assert data == data2
