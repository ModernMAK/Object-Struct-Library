import itertools
import struct
from dataclasses import field, is_dataclass
from enum import Enum, IntEnum, IntFlag
from io import BytesIO
from typing import List

import pytest

from structlib.datastruct import enumstruct, datastruct
from structlib.typedef import calculate_padding, align_of, native_size_of, annotation_of, size_of
from structlib.typedefs.integer import IntegerDefinition
from structlib.typedefs.padding import PaddingDefinition, Const
from structlib.typedefs.strings import ByteBuffer

UInt32 = IntegerDefinition(4, False, alignment=1, byteorder="little")
ByteArray4 = ByteBuffer(4, alignment=1)


@enumstruct(backing_type=ByteArray4)
class DDSFourCC(Enum):
    DXT1 = b"DXT1"
    DXT2 = b"DXT2"
    DXT3 = b"DXT3"
    DXT4 = b"DXT4"
    DXT5 = b"DXT5"
    DX10 = b"DX10"
    Extended = DX10


@enumstruct(backing_type=UInt32)
class DXGIFormat(IntEnum):
    BC1_TYPELESS = 70
    BC2_TYPELESS = 73
    BC3_TYPELESS = 76
    BC4_TYPELESS = 79
    BC5_TYPELESS = 82
    BC6H_TYPELESS = 94
    BC7_TYPELESS = 97


@enumstruct(backing_type=UInt32)
class ResourceDimension(IntEnum):
    UNKNOWN = 0
    BUFFER = 1
    TEXTURE1D = 2
    TEXTURE2D = 3
    TEXTURE3D = 4


@enumstruct(backing_type=UInt32)
class DDSD(IntFlag):
    CAPS = 0x1
    HEIGHT = 0x2
    WIDTH = 0x4
    PITCH = 0x8
    PIXEL_FORMAT = 0x1000
    MIPMAP_COUNT = 0x20000
    LINEAR_SIZE = 0x80000
    DEPTH = 0x800000


@enumstruct(backing_type=UInt32)
class DDPF(IntFlag):
    ALPHA_PIXELS = 0x1
    FOURCC = 0x4
    RGB = 0x40


@enumstruct(backing_type=UInt32)
class DDCaps(IntFlag):
    COMPLEX = 0x8
    TEXTURE = 0x1000
    MIPMAP = 0x400000


@enumstruct(backing_type=UInt32)
class DDCaps2(IntFlag):
    CUBEMAP = 0x200
    CUBEMAP_POS_X = 0x400
    CUBEMAP_NEG_X = 0x800
    CUBEMAP_POS_Y = 0x1000
    CUBEMAP_NEG_Y = 0x2000
    CUBEMAP_POS_Z = 0x4000
    CUBEMAP_NEG_Z = 0x8000
    VOLUME = 0x200000


NullPad8 = PaddingDefinition(pad_size=8)


@datastruct(alignment=1)
class DDSCaps:
    # _LAYOUT: ClassVar = Struct("<I I 8x")
    caps: DDCaps
    caps2: DDCaps2
    _padding: NullPad8  # = field(init=False, repr=False, hash=False, compare=False)
    #
    # @classmethod
    # def unpack(cls, buffer: bytes) -> DDSCaps:
    #     args = cls._LAYOUT.unpack(buffer)
    #     caps_buffer, caps2_buffer = args
    #     caps = DDCaps(caps_buffer)
    #     caps2 = DDCaps2(caps2_buffer)
    #     return cls(caps, caps2)
    #
    # def to_args(self) -> Tuple:
    #     return self.caps, self.caps2
    #
    # def pack(self) -> bytes:
    #     args = self.to_args()
    #     return self._LAYOUT.pack(*args)


_DDPixelFormat_SIZE = Const(UInt32, 32)


#
@datastruct(alignment=1)
class DDPixelFormat:
    # _LAYOUT: ClassVar = Struct("<I I 4s I 4I")

    # @property
    # def size(self) -> int:
    #     return self._LAYOUT.size

    size: _DDPixelFormat_SIZE
    flags: DDPF
    fourCC: DDSFourCC
    rgb_bit_count: UInt32 = 0
    r_mask: UInt32 = 0x0
    g_mask: UInt32 = 0x0
    b_mask: UInt32 = 0x0
    a_mask: UInt32 = 0x0


_DDSHeader_SIZE = Const(UInt32, 124)


@datastruct(alignment=1)
class DDSHeader:
    # @property
    # def size(self) -> int:
    #     return self._LAYOUT.size
    size: _DDSHeader_SIZE
    flags: DDSD
    height: UInt32
    width: UInt32
    pitch_or_linear_size: UInt32
    depth: UInt32
    mipmap_count: UInt32
    pixel_format: DDPixelFormat
    caps: DDSCaps
    #
    # def to_args(self) -> Tuple:
    #     return self.size, self.flags.value, self.height, self.width, self.pitch_or_linear_size, self.depth, self.mipmap_count, self.pixel_format.pack(), self.caps.pack()
    #
    # def pack(self) -> bytes:
    #     args = self.to_args()
    #     return self._LAYOUT.pack(*args)
    #
    # @classmethod
    # def unpack(cls, buffer: bytes) -> DDSHeader:
    #     args = cls._LAYOUT.unpack(buffer)
    #     size, flags, height, width, pitch_or_linear, depth, mipmap_count, pixel_format_buffer, caps_buffer = args
    #     pixel_format = DDPixelFormat.unpack(pixel_format_buffer)
    #     caps = DDSCaps.unpack(caps_buffer)
    #     return cls(flags, height, width, pitch_or_linear, depth, mipmap_count, pixel_format, caps)


#
#     def to_args(self) -> Tuple:
#         return self.size, self.flags.value, self.fourCC.value, self.rgb_bit_count, self.r_mask, self.g_mask, self.b_mask, self.a_mask
#
#     def pack(self) -> bytes:
#         args = self.to_args()
#         return self._LAYOUT.pack(*args)
#
#     @classmethod
#     def unpack(cls, buffer: bytes) -> DDPixelFormat:
#         args = cls._LAYOUT.unpack(buffer)
#         size, flags_buffer, fourcc_buffer, bit_count, r, g, b, a = args
#         fourcc = DDSFourCC(fourcc_buffer)
#         flags = DDPF(flags_buffer)
#         return cls(flags, fourcc, bit_count, r, g, b, a)
#

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


def _pretty_ids(name_or_dclass, values):
    if is_dataclass(name_or_dclass):
        return [str(name_or_dclass(*v) for v in values)]
    else:
        return [f"({name_or_dclass}={str(v)})" for v in values]


def all_combinations(f: List):
    for l in range(len(f) + 1):
        yield from itertools.combinations(f, l)


def all_flag_combinations(f: List):
    for t in all_combinations(f):
        flag = 0
        for val in t:
            flag |= val
        yield flag


def _enum2list(t) -> List:
    return [e for e in t]


def _iterflags(f: List):
    if len(f) == 1:
        yield f[0]
    else:
        subset = f[1:]
        flag = f[0]

        yield flag

        for subflag in _iterflags(subset):
            yield flag | subflag

        yield from _iterflags(subset)

def _flagprod(t):
    f = _enum2list(t)
    return _iterflags(f)


DDCAPS_ARGS = list(all_flag_combinations([DDCaps.COMPLEX, DDCaps.TEXTURE, DDCaps.MIPMAP]))
DDCAPS2_ARGS = list(all_flag_combinations(
    [DDCaps2.CUBEMAP, DDCaps2.VOLUME, DDCaps2.CUBEMAP_NEG_X, DDCaps2.CUBEMAP_POS_X, DDCaps2.CUBEMAP_NEG_Y,
     DDCaps2.CUBEMAP_POS_Y, DDCaps2.CUBEMAP_NEG_Z, DDCaps2.CUBEMAP_POS_Z]))

DDSCaps_ARGS = list(itertools.product(DDCAPS_ARGS, DDCAPS2_ARGS))
DDSCAPS_ARGS_IDS = _pretty_ids(DDSCaps, DDSCaps_ARGS)

_ORIGINS = [0, 1, 2]
_OFFSETS = [0, 1, 2]
_ORIGIN_IDS = _pretty_ids("Origin", _ORIGINS)
_OFFSET_IDS = _pretty_ids("Offset", _OFFSETS)

DDSD_ARGS = []
_UINT32_RANGE = [0, 0xffffffff]
DDSHeader_HEIGHT_ARGS = _UINT32_RANGE
DDSHeader_WIDTH_ARGS = _UINT32_RANGE
DDSHeader_PoLSIZE_ARGS = _UINT32_RANGE
DDSHeader_DEPTH_ARGS = _UINT32_RANGE
DDSHeader_MIPMAP_ARGS = _UINT32_RANGE

DDPF_ARGS = _flagprod(DDPF)#_iterflags([DDPF.ALPHA_PIXELS, DDPF.FOURCC, DDPF.RGB])
DDSFourCC_ARGS = _enum2list(DDSFourCC)
DDPixelFormat_BIT_COUNT_ARGS = _UINT32_RANGE
DDPixelFormat_R_ARGS = _UINT32_RANGE
DDPixelFormat_G_ARGS = _UINT32_RANGE
DDPixelFormat_B_ARGS = _UINT32_RANGE
DDPixelFormat_A_ARGS = _UINT32_RANGE

DDPixelFormat_ARGS = list(
    itertools.product(DDPF_ARGS, DDSFourCC_ARGS, DDPixelFormat_BIT_COUNT_ARGS, DDPixelFormat_R_ARGS,
                      DDPixelFormat_G_ARGS, DDPixelFormat_B_ARGS, DDPixelFormat_A_ARGS))

DDSHeader_ARGS = list(itertools.product(DDSD_ARGS, DDSHeader_HEIGHT_ARGS, DDSHeader_WIDTH_ARGS, DDSHeader_PoLSIZE_ARGS,
                                        DDSHeader_DEPTH_ARGS, DDSHeader_MIPMAP_ARGS, DDPixelFormat_ARGS, DDSCaps_ARGS))

DDSHeader_IDS = _pretty_ids(DDSHeader,DDSHeader_ARGS)

class TestDDSHeader(DataStructTests):
    _s = struct.Struct("<7I 44x 32s 16s 4x")

    @classmethod
    def _emulate_pack(cls, _arg):
        true_args = [a.value if hasattr(a, "value") else a for a in _arg]
        return cls._s.pack(*true_args)

    @pytest.fixture
    def typedef(self):
        return DDSHeader

    @pytest.fixture(params=DDSHeader_ARGS, ids=DDSHeader_IDS)
    def arg(self, request):
        return request.param

    @pytest.fixture
    def typedef_alignment(self):
        return 1

    @pytest.fixture
    def typedef_native_size(self):
        return 16

    @pytest.fixture
    def typedef_size(self):
        return 16

    @pytest.fixture(params=_OFFSETS, ids=_OFFSET_IDS)
    def offset(self, request):
        return request.param

    @pytest.fixture(params=_ORIGINS, ids=_ORIGIN_IDS)
    def origin(self, request):
        return request.param
