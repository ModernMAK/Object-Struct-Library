from __future__ import annotations

import sys
from enum import Enum, Flag, IntFlag
from typing import Literal, Tuple

from structlib.types import BufferApiType, BufferStream


def flip_endian(b: bytes) -> bytes:
    return bytes(b[-i] for i in range(len(b)))


# OH, GOD. ALIGNMENT IS HARDER THAN I THOUGHT
# https://en.wikipedia.org/wiki/Data_structure_alignment

# SO;
# Byte order doesn't matter to packing
# Size doesn't matter either; (only the written size)
# Align, or Not

# So... Every struct specifies an alignment
#   But then how to handle nesting / multi-layout?
#       Multi-Layout

# MULTI-LAYOUT
#   If align,


def calculate_padding(offset: int, alignment: int = 1) -> int:
    return (alignment - (offset % alignment)) % alignment


# how to handle alignment
# assuming byte written
#   E.G.
#       3 bytes written, alignment 1
#   E.G.
#       6 bytes written, alignment 2
# MultiLayout
#   E.G.
#       10 bytes written, alignment 4


# I think I got it,
#   and I already have the code to do it!

class ByteFlags(Flag):
    LittleEndian = 0b0
    BigEndian = 0b1
    NetworkEndian = BigEndian
    NativeEndian = (BigEndian if sys.byteorder == "big" else LittleEndian)  # Dynamically set native to 'little' or 'big'

    @classmethod
    def parse_endian(cls, literal: Literal["little", "big"]) -> ByteFlags:
        return cls.BigEndian if literal == "big" else cls.LittleEndian

    @property
    def endian_literal(self) -> Literal["little", "big"]:
        return "big" if ByteFlags.BigEndian in self else "little"

    Aligned = 0b10
    # Unaligned = 0b00

    # NativeSize = 0b000
    StandardSize = 0b100


def apply_padding(data: bytes, flags: ByteFlags, alignment: int = 1, index: int = 0) -> bytes:
    if alignment in [0, 1] or index == 0 or index % alignment == 0 or ByteFlags.Aligned not in flags:
        return data  # special cases, do nothing
    else:
        padding = calculate_padding(index, alignment)
        return bytes(b"\x00" * padding) + data


def remove_padding(data: bytes, flags: ByteFlags, alignment: int = 1, index: int = 0) -> bytes:
    if alignment in [0, 1] or index == 0 or index % alignment == 0 or ByteFlags.Aligned not in flags:
        return data  # special cases, do nothing
    else:
        padding = calculate_padding(index, alignment)
        return data[padding:]

