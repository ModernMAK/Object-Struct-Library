from io import BytesIO

from structlib import bufferio
from structlib.byteorder import ByteOrder, resolve_byteorder
from structlib.packing import Packable
from structlib.typedef import TypeDefAlignable, align_as, align_of, TypeDefByteOrder, byteorder_as, byteorder_of


class AlignmentTests:
    @staticmethod
    def test_align_as(alignable_typedef: TypeDefAlignable, alignment: int):
        aligned_typedef = align_as(alignable_typedef, alignment)
        assert (
            align_of(aligned_typedef) == alignment
        ), "`align_of` not getting value set by `align_as`!"

    @staticmethod
    def test_align_as_equality(alignable_typedef: TypeDefAlignable, alignment: int):
        src_align = align_of(alignable_typedef)
        new_t = align_as(alignable_typedef, alignment)
        redef_t = align_as(new_t, src_align)
        assert (
            alignable_typedef == redef_t
        ), "Same alignment should preserve equality of object!"

    @staticmethod
    def test_align_as_inequality(alignable_typedef: TypeDefAlignable, alignment: int):
        src_align = align_of(alignable_typedef)
        new_t = align_as(alignable_typedef, alignment)
        if src_align != alignment:
            assert (
                alignable_typedef != new_t
            ), "Differing alignment should break equality of object!"

    @staticmethod
    def test_align_as_preserves_type(
        alignable_typedef: TypeDefAlignable, alignment: int
    ):
        # A new types should be returned by align_as,
        # unless alignment does not change,
        # then the same type `should` be returned
        src_alignment = align_of(alignable_typedef)
        new_t = align_as(alignable_typedef, alignment)
        if src_alignment == alignment:  # Expect same instance
            assert (
                new_t is alignable_typedef
            ), "`align_as` should not alter input `type-object` but a new `type-object` was returned!"
        else:  # Expect new instance
            assert (
                new_t is not alignable_typedef
            ), "`align_as` should not alter input `type-object` but a new `type-object` was NOT returned!"


class ByteorderTests:
    @staticmethod
    def test_byteorder_as(byteorder_typedef: TypeDefByteOrder, byteorder: ByteOrder):
        new_t = byteorder_as(byteorder_typedef, byteorder)
        assert byteorder_of(new_t) == resolve_byteorder(
            byteorder
        ), "'byteorder_of' not getting value set by 'byteorder_as'!"

    @staticmethod
    def test_byteorder_as_preserves_type(
        byteorder_typedef: TypeDefByteOrder, byteorder: ByteOrder
    ):
        # A new types should be returned by byteorder_as
        # unless byteorder does not change
        # then the same type `should` be returned
        src_byteorder = byteorder_of(byteorder_typedef)
        new_t = byteorder_as(byteorder_typedef, byteorder)
        if src_byteorder == resolve_byteorder(byteorder):
            assert (
                new_t is byteorder_typedef
            ), f"'{byteorder_typedef.__class__}' should return the same instance if byteorder does not change!"
        else:
            assert (
                new_t is not byteorder_typedef
            ), "`byteorder_as` should not alter input `type-object`"

    @staticmethod
    def test_byteorder_as_equality(
        byteorder_typedef: TypeDefByteOrder, byteorder: ByteOrder
    ):
        src_byteorder = byteorder_of(byteorder_typedef)
        new_t = byteorder_as(byteorder_typedef, byteorder)
        redef_t = byteorder_as(new_t, src_byteorder)
        assert (
            byteorder_typedef == redef_t
        ), "Same byteorder should preserve equality of object!"

    @staticmethod
    def test_byteorder_as_inequality(
        byteorder_typedef: TypeDefByteOrder, byteorder: ByteOrder
    ):
        src_byteorder = byteorder_of(byteorder_typedef)
        new_t = byteorder_as(byteorder_typedef, byteorder)
        if src_byteorder != resolve_byteorder(byteorder):
            assert (
                byteorder_typedef != new_t
            ), "Differing byteorder should break equality of object!"


class TypedefEqualityTests:
    @staticmethod
    def test_definition_equality(typedef, equal_typedef):
        assert typedef == equal_typedef


class TypedefInequalityTests:
    @staticmethod
    def test_definition_inequality(typedef, unequal_typedef):
        assert typedef != unequal_typedef
        # _DEF = self.DEFINITION
        # if _DEF is not None:
        #     for _def in self.INEQUAL_DEFINITIONS:
        #         assert _def != _DEF


class PackableTests:
    @staticmethod
    def test_pack(typedef: Packable, sample, buffer):
        packed = typedef.pack(sample)
        assert packed == buffer

    @staticmethod
    def test_unpack(typedef: Packable, sample, buffer):
        unpacked = typedef.unpack(buffer)
        assert unpacked == sample

    # TODO Move to seperate class
    #   Just like Equality/Inequality, this Test class would be too cluttered with it
    # def test_pack_equality(self):
    #     samples = self.SAMPLES
    #     typedef_groups = self.get_all_typdef_groups()
    #     for typedefs in typedef_groups:
    #         for i in range(
    #                 len(typedefs) - 1
    #         ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #             left, right = typedefs[i], typedefs[i + 1]
    #             assert_pack_equality(left, right, samples)
    # def test_unpack_equality(self):
    #     samples = self.SAMPLES
    #     typedef_groups = self.get_all_typdef_groups()
    #     s2bs = self.get_all_sample2bytes(self.ALIGN)
    #     for typedefs, s2b in zip(typedef_groups, s2bs):
    #         for i in range(
    #                 len(typedefs) - 1
    #         ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #             left, right = typedefs[i], typedefs[i + 1]
    #             assert_unpack_equality(left, right, s2b, samples)
    #


def _emulate_pack_into_buffer(buffer, origin, offset, alignment):
    """
    Returns the written amount & emulated buffer
    """
    prefix = bufferio.calculate_padding(alignment, offset)
    data_size = len(buffer)
    postfix = bufferio.calculate_padding(alignment, data_size)
    written = prefix + postfix + data_size
    size = origin + offset + written
    emulated_buffer = bytearray(b"\0" * size)
    emulated_buffer[
        origin + offset + prefix : origin + offset + prefix + data_size
    ] = buffer
    return written, emulated_buffer


class IOPackableTests:
    @staticmethod
    def test_pack_into_buffer(
        typedef: Packable, sample, buffer, origin, offset, alignment
    ):
        expected_written, expected = _emulate_pack_into_buffer(
            buffer, origin, offset, alignment
        )
        aligned_typedef = align_as(typedef, alignment)
        writable = bytearray(b"\0" * len(expected))
        written = aligned_typedef.pack_into(
            writable, sample, offset=offset, origin=origin
        )
        assert writable == expected, (writable, expected)
        assert written == expected_written, (written, expected_written)

    @staticmethod
    def test_pack_into_stream(
        typedef: Packable, sample, buffer, origin, offset, alignment
    ):
        expected_written, expected = _emulate_pack_into_buffer(
            buffer, origin, offset, alignment
        )
        aligned_typedef = align_as(typedef, alignment)
        with BytesIO() as writable:
            writable.write(b"\0" * (origin + offset))
            written = aligned_typedef.pack_into(writable, sample, origin=origin)
            writable.seek(0)
            write_buffer = writable.read()
            assert written == expected_written
            assert write_buffer == expected

    @staticmethod
    def test_unpack_from_buffer(
        typedef: Packable, sample, buffer, origin, offset, alignment
    ):
        expected_read, readable = _emulate_pack_into_buffer(
            buffer, origin, offset, alignment
        )
        aligned_typedef = align_as(typedef, alignment)
        read, value = aligned_typedef.unpack_from(
            readable, offset=offset, origin=origin
        )
        assert value == sample
        assert read == expected_read

    @staticmethod
    def test_unpack_from_stream(
        typedef: Packable, sample, buffer, origin, offset, alignment
    ):
        expected_read, emulated = _emulate_pack_into_buffer(
            buffer, origin, offset, alignment
        )
        aligned_typedef = align_as(typedef, alignment)
        with BytesIO(emulated) as readable:
            readable.seek(origin + offset)
            read, value = aligned_typedef.unpack_from(readable, origin=origin)
            assert read == expected_read
            assert value == sample

    # def test_buffer_pack_equality(self):
    #     samples = self.SAMPLES
    #     get_buf = self.get_empty_buffer_generator()
    #     typedef_groups = self.get_all_typdef_groups()
    #     # s2bs = self.get_all_sample2bytes(self.ALIGN)
    #
    #     for origin in self.ORIGINS:
    #         for offset in self.OFFSETS:
    #             for typedefs in typedef_groups:
    #                 for i in range(
    #                         len(typedefs) - 1
    #                 ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                     left, right = typedefs[i], typedefs[i + 1]
    #                     assert_buffer_pack_equality(
    #                         left, right, get_buf, samples, self.ALIGN, offset, origin
    #                     )
    #
    #             for align in self.ALIGNMENTS:
    #                 for typedefs in typedef_groups:
    #                     aligned_typedefs = align_as_many(*typedefs, align=align)
    #                     for i in range(
    #                             len(aligned_typedefs) - 1
    #                     ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                         left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
    #                         assert_buffer_pack_equality(
    #                             left, right, get_buf, samples, align, offset, origin
    #                         )
    #
    # def test_buffer_unpack_equality(self):
    #     samples = self.SAMPLES
    #     get_buf = self.get_empty_buffer_generator()
    #     typedef_groups = self.get_all_typdef_groups()
    #     s2bs = self.get_all_sample2bytes(self.ALIGN)
    #
    #     for origin in self.ORIGINS:
    #         for offset in self.OFFSETS:
    #             for typedefs, s2b in zip(typedef_groups, s2bs):
    #                 for i in range(
    #                         len(typedefs) - 1
    #                 ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                     left, right = typedefs[i], typedefs[i + 1]
    #                     assert_buffer_unpack_equality(
    #                         left,
    #                         right,
    #                         get_buf,
    #                         s2b,
    #                         samples,
    #                         self.ALIGN,
    #                         offset,
    #                         origin,
    #                     )
    #
    #             for align in self.ALIGNMENTS:
    #                 aligned_s2bs = self.get_all_sample2bytes(align)
    #                 for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
    #                     aligned_typedefs = align_as_many(*typedefs, align=align)
    #                     for i in range(
    #                             len(aligned_typedefs) - 1
    #                     ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                         left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
    #                         assert_buffer_unpack_equality(
    #                             left,
    #                             right,
    #                             get_buf,
    #                             s2b,
    #                             samples,
    #                             align,
    #                             offset,
    #                             origin,
    #                         )
    #
    # def test_stream_pack_equality(self):
    #     samples = self.SAMPLES
    #     get_buf = self.get_empty_buffer_generator()
    #     typedef_groups = self.get_all_typdef_groups()
    #     # s2bs = self.get_all_sample2bytes(self.ALIGN)
    #
    #     for origin in self.ORIGINS:
    #         for offset in self.OFFSETS:
    #             for typedefs in typedef_groups:
    #                 for i in range(
    #                         len(typedefs) - 1
    #                 ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                     left, right = typedefs[i], typedefs[i + 1]
    #                     assert_stream_pack_equality(
    #                         left, right, get_buf, samples, self.ALIGN, offset, origin
    #                     )
    #
    #             for align in self.ALIGNMENTS:
    #                 for typedefs in typedef_groups:
    #                     aligned_typedefs = align_as_many(*typedefs, align=align)
    #                     for i in range(
    #                             len(aligned_typedefs) - 1
    #                     ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                         left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
    #                         assert_stream_pack_equality(
    #                             left, right, get_buf, samples, align, offset, origin
    #                         )
    #
    # def test_stream_unpack_equality(self):
    #     samples = self.SAMPLES
    #     get_buf = self.get_empty_buffer_generator()
    #     typedef_groups = self.get_all_typdef_groups()
    #     s2bs = self.get_all_sample2bytes(self.ALIGN)
    #
    #     for origin in self.ORIGINS:
    #         for offset in self.OFFSETS:
    #             for typedefs, s2b in zip(typedef_groups, s2bs):
    #                 for i in range(
    #                         len(typedefs) - 1
    #                 ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                     left, right = typedefs[i], typedefs[i + 1]
    #                     assert_stream_unpack_equality(
    #                         left,
    #                         right,
    #                         get_buf,
    #                         s2b,
    #                         samples,
    #                         self.ALIGN,
    #                         offset,
    #                         origin,
    #                     )
    #
    #             for align in self.ALIGNMENTS:
    #                 aligned_s2bs = self.get_all_sample2bytes(align)
    #                 for typedefs, s2b in zip(typedef_groups, aligned_s2bs):
    #                     aligned_typedefs = align_as_many(*typedefs, align=align)
    #                     for i in range(
    #                             len(aligned_typedefs) - 1
    #                     ):  # We don't need to do an N*N comparisons; if each is equal to the previous, they are all equal by induction
    #                         left, right = aligned_typedefs[i], aligned_typedefs[i + 1]
    #                         assert_stream_unpack_equality(
    #                             left,
    #                             right,
    #                             get_buf,
    #                             s2b,
    #                             samples,
    #                             align,
    #                             offset,
    #                             origin,
    #                         )
