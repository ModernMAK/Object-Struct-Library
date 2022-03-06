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
