import itertools
from enum import IntEnum

import pytest

from structlib.byteorder import ByteOrder
from structlib.datastruct import datastruct, enumstruct
from structlib.typedef import size_of
from structlib.typedefs.integer import IntegerDefinition
from structlib.typedefs.strings import CStringBuffer
from structlib.typedefs.structure import Struct

_SGA_BOM: ByteOrder = "little"
UInt32 = IntegerDefinition(byte_size=4, signed=False, byteorder=_SGA_BOM)
UInt16 = IntegerDefinition(byte_size=2, signed=False, byteorder=_SGA_BOM)
TocRange = Struct(UInt16, UInt16, alignment=1)
DriveString = CStringBuffer(64, encoding="ascii", alignment=1)
_UInt32Max = (2 ** 32) - 1
_UInt16Max = (2 ** 16) - 1


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


@pytest.mark.parametrize("length_on_disk", [0, _UInt32Max])
@pytest.mark.parametrize("length_in_archive", [0, _UInt32Max])
@pytest.mark.parametrize("data_pos", [0, _UInt32Max])
@pytest.mark.parametrize("storage_type", [StorageType.None_, StorageType.Buffer, StorageType.Stream])
@pytest.mark.parametrize("name_pos", [0, _UInt32Max])
class TestFileDef:
    @staticmethod
    def test_size(name_pos: int, storage_type: int, data_pos: int, length_in_archive: int, length_on_disk):
        args = (name_pos, storage_type, data_pos, length_in_archive, length_on_disk)
        inst = FileDef(*args)
        assert size_of(inst) == 20

    @staticmethod
    def test_pack_symmetry(name_pos: int, storage_type: int, data_pos: int, length_in_archive: int, length_on_disk):
        args = (name_pos, storage_type, data_pos, length_in_archive, length_on_disk)
        inst = FileDef(*args)
        packed = inst.pack()
        unpacked = inst.unpack(packed)
        assert unpacked == inst

    @staticmethod
    def test_pack_class(name_pos: int, storage_type: int, data_pos: int, length_in_archive: int, length_on_disk):
        args = (name_pos, storage_type, data_pos, length_in_archive, length_on_disk)
        inst = FileDef(*args)
        packed = FileDef.pack(inst)
        unpacked = inst.unpack(packed)
        assert unpacked == inst


@pytest.mark.parametrize("file_range", list(itertools.permutations([0, _UInt16Max], 2)))
@pytest.mark.parametrize("folder_range", list(itertools.permutations([0, _UInt16Max], 2)))
@pytest.mark.parametrize("root_folder", [0, _UInt16Max])
@pytest.mark.parametrize("alias", ["Drive Alias", "Test Alias"])
@pytest.mark.parametrize("name", ["Drive Name", "Test Name"])
class TestDriveDef:
    @staticmethod
    def test_size(alias, name, root_folder, folder_range, file_range):
        args = (alias, name, root_folder, folder_range, file_range)
        inst = DriveDef(*args)
        assert size_of(inst) == 138

    @staticmethod
    def test_pack_symmetry(alias, name, root_folder, folder_range, file_range):
        args = (alias, name, root_folder, folder_range, file_range)
        inst = DriveDef(*args)
        packed = inst.pack()
        unpacked = inst.unpack(packed)
        assert unpacked == inst
