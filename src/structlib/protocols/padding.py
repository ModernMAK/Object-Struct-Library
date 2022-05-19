from structlib.protocols import AlignLike, align_of


def padding_of(alignable: AlignLike, offset: int) -> int:
    return calculate_padding(align_of(alignable), offset)


def calculate_padding(align_as: int, offset: int) -> int:
    bytes_from_align = offset % align_as
    if bytes_from_align != 0:
        return align_as - bytes_from_align
    else:
        return 0
