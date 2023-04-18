import itertools
import struct
from enum import IntEnum
from io import BytesIO

import pytest

from structlib.byteorder import ByteOrder
from structlib.datastruct import datastruct, enumstruct
from structlib.typedef import (
    size_of,
    calculate_padding,
    align_as,
    align_of,
    native_size_of,
    annotation_of,
)
from structlib.typedefs.integer import IntegerDefinition
from structlib.typedefs.strings import CStringBuffer
from structlib.typedefs.structure import Struct

_SGA_BOM: ByteOrder = "little"
UInt32 = IntegerDefinition(byte_size=4, signed=False, byteorder=_SGA_BOM)
UInt16 = IntegerDefinition(byte_size=2, signed=False, byteorder=_SGA_BOM)
TocRange = Struct(UInt16, UInt16, alignment=1)
DriveString = CStringBuffer(64, encoding="ascii", alignment=1)
_UInt32Max = (2**32) - 1
_UInt16Max = (2**16) - 1


@enumstruct(backing_type=UInt32)
class StorageType(IntEnum):
    None_ = 0
    Buffer = 16
    Stream = 32


@datastruct(alignment=1)
class FileDef:
    name_pos: UInt32
    storage_type: StorageType
    data_pos: UInt32
    length_in_archive: UInt32
    length_on_disk: UInt32


@datastruct(alignment=1)
class FolderDef:
    name_pos: UInt32
    folder_range: TocRange
    file_range: TocRange


@datastruct(alignment=1)
class DriveDef:
    alias: DriveString
    name: DriveString
    root_folder: UInt16
    folder_range: TocRange
    file_range: TocRange


_ORIGINS = [0, 1, 2]
_OFFSETS = [0, 1, 2]
_ALIGNMENTS = [1, 2, 4]


class DataStructTests:
    @classmethod
    def _emulate_pack(cls, _arg):
        raise NotImplementedError

    @classmethod
    def _emulate_nonaligned(
        cls, _buffer: bytes, _origin: int, _offset: int, _alignment: int
    ):
        aligned_offset = _offset + calculate_padding(_alignment, _offset)
        size = len(_buffer)
        aligned_size = size + calculate_padding(_alignment, size)
        full_size = _origin + aligned_offset + aligned_size
        emu = bytearray(b"\0" * full_size)
        start = _origin + aligned_offset
        end = start + size
        emu[start:end] = _buffer
        return (full_size - (_offset + _origin)), emu

    def test_pack_self(self, typedef, arg):
        expected = self._emulate_pack(arg)
        inst = typedef(*arg)
        packed = inst.pack()
        assert packed == expected

    def test_pack_cls(self, typedef, arg):
        expected = self._emulate_pack(arg)
        inst = typedef(*arg)
        packed = typedef.pack(inst)
        assert packed == expected

    @staticmethod
    def test_instance_symmetry(typedef, arg):
        inst = typedef(*arg)
        packed = inst.pack()
        unpacked = typedef.unpack(packed)
        assert unpacked == inst

    def test_buffer_symmetry(self, typedef, arg):
        expected = self._emulate_pack(arg)
        inst = typedef.unpack(expected)
        packed = inst.pack()
        assert packed == expected

    def test_pack_into_stream(self, typedef, arg, origin: int, offset: int):
        raw = self._emulate_pack(arg)
        expected_write, expected_buffer = self._emulate_nonaligned(
            raw, origin, offset, align_of(typedef)
        )
        inst = typedef(*arg)
        with BytesIO() as stream:
            stream.write(b"\0" * (origin + offset))
            wrote = inst.pack_into(stream, origin=origin)
            assert wrote == expected_write
            stream.seek(0)
            wrote_buffer = stream.read()
            assert wrote_buffer == expected_buffer

    def test_pack_into_buffer(self, typedef, arg, origin: int, offset: int):
        raw = self._emulate_pack(arg)
        expected_write, expected_buffer = self._emulate_nonaligned(
            raw, origin, offset, align_of(typedef)
        )
        inst = typedef(*arg)
        wrote_buffer = bytearray(len(expected_buffer))
        wrote = inst.pack_into(wrote_buffer, origin=origin, offset=offset)
        assert wrote == expected_write
        assert wrote_buffer == expected_buffer

    def test_unpack_from_stream(self, typedef, arg, origin: int, offset: int):
        raw = self._emulate_pack(arg)
        expected_read, read_buffer = self._emulate_nonaligned(
            raw, origin, offset, align_of(typedef)
        )
        expected_inst = typedef(*arg)
        with BytesIO(read_buffer) as stream:
            stream.seek(origin + offset)
            read, read_inst = typedef.unpack_from(stream, origin=origin)
            assert read == expected_read
            assert read_inst == expected_inst

    def test_unpack_from_buffer(self, typedef, arg, origin: int, offset: int):
        raw = self._emulate_pack(arg)
        expected_read, read_buffer = self._emulate_nonaligned(
            raw, origin, offset, align_of(typedef)
        )
        expected_inst = typedef(*arg)
        read, read_inst = typedef.unpack_from(read_buffer, origin=origin, offset=offset)
        assert read == expected_read
        assert read_inst == expected_inst

    def test_native_size_of(self, typedef, typedef_native_size):
        if typedef_native_size is None:
            return  # For dynamiclly sized typedefs

        actual_native_size = native_size_of(typedef)
        assert actual_native_size == typedef_native_size

    def test_annotation(self, typedef):
        annotation = annotation_of(typedef)
        assert annotation == typedef

    def test_size_of(self, typedef, typedef_size):
        if typedef_size is None:
            return  # For dynamically sized typedefs
        actual_size = size_of(typedef)
        assert actual_size == typedef_size

    def test_alignment(self, typedef, typedef_alignment):
        actual_alignment = align_of(typedef)
        assert actual_alignment == typedef_alignment


def _pretty_ids(name, values):
    return [f"({name}={v})" for v in values]


_NAME_POS = [0, _UInt32Max]
_STORAGE_TYPE = [StorageType.None_, StorageType.Buffer, StorageType.Stream]
_DATA_POS = [0, _UInt32Max]
_LEN_IN_ARCHIVE = [0, _UInt32Max]
_LEN_ON_DISK = [0, _UInt32Max]
FILEDEF_ARGS = list(
    itertools.product(
        _NAME_POS, _STORAGE_TYPE, _DATA_POS, _LEN_IN_ARCHIVE, _LEN_ON_DISK
    )
)
FILEDEF_ARG_IDS = [str(FileDef(*arg)) for arg in FILEDEF_ARGS]
_OFFSET_IDS = _pretty_ids("offset", _OFFSETS)
_ORIGIN_IDS = _pretty_ids("origin", _ORIGINS)


# @pytest.mark.parametrize("arg", FILEDEF_ARGS, ids=FILEDEF_ARG_IDS)
class TestFileDef(DataStructTests):
    _s = struct.Struct(f"<5I")

    @pytest.fixture(params=FILEDEF_ARGS, ids=FILEDEF_ARG_IDS)
    def arg(self, request):
        return request.param

    @classmethod
    def _emulate_pack(cls, _arg):
        return cls._s.pack(*_arg)

    @pytest.fixture
    def typedef(self):
        return FileDef

    @pytest.fixture(params=_OFFSETS, ids=_OFFSET_IDS)
    def offset(self, request):
        return request.param

    @pytest.fixture(params=_ORIGINS, ids=_ORIGIN_IDS)
    def origin(self, request):
        return request.param

    @pytest.fixture
    def typedef_native_size(self):
        __PARAMS = 5
        __UINT32_SIZE = 4
        return __PARAMS * __UINT32_SIZE

    @pytest.fixture
    def typedef_size(self, typedef_native_size):
        return typedef_native_size  # same for this typedef

    @pytest.fixture
    def typedef_alignment(self):
        return 1


_FILE_RANGE = list(itertools.permutations([0, _UInt16Max], 2))
_FOLDER_RANGE = list(itertools.permutations([0, _UInt16Max], 2))
_ROOT_FOLDER = [0, _UInt16Max]
_ALIAS = ["Drive Alias", "Test Alias"]
_NAME = ["Drive Name", "Test Name"]
_DRIVEDEF_ARGS = list(
    itertools.product(_ALIAS, _NAME, _ROOT_FOLDER, _FOLDER_RANGE, _FILE_RANGE)
)
_DRIVEDEF_ARG_IDS = [str(DriveDef(*arg)) for arg in _DRIVEDEF_ARGS]


class TestDriveDef(DataStructTests):
    _s = struct.Struct("<64s 64s 5H")

    @pytest.fixture
    def typedef(self):
        return DriveDef

    @pytest.fixture(params=_DRIVEDEF_ARGS, ids=_DRIVEDEF_ARG_IDS)
    def arg(self, request):
        return request.param

    @pytest.fixture
    def typedef_native_size(self):
        return 138

    @pytest.fixture
    def typedef_size(self, typedef_native_size):
        return typedef_native_size

    @classmethod
    def _emulate_pack(cls, _arg):
        s_arg = (
            _arg[0].encode("ascii"),
            _arg[1].encode("ascii"),
            _arg[2],
            _arg[3][0],
            _arg[3][1],
            _arg[4][0],
            _arg[4][1],
        )
        return cls._s.pack(*s_arg)

    @pytest.fixture
    def typedef_alignment(self):
        return 1

    @pytest.fixture(params=_OFFSETS, ids=_OFFSET_IDS)
    def offset(self, request):
        return request.param

    @pytest.fixture(params=_ORIGINS, ids=_ORIGIN_IDS)
    def origin(self, request):
        return request.param
