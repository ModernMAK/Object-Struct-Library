import warnings
from typing import Any, List

from tests.typedefs.util import classproperty
from structlib.byteorder import ByteOrder, resolve_byteorder, NativeEndian, NetworkEndian, BigEndian, LittleEndian
from structlib.protocols.typedef import byteorder_as, byteorder_of, TypeDefByteOrder


# AVOID using test as prefix
class ByteorderTests:
    @classproperty
    def BYTEORDER_TYPEDEFS(self) -> List[TypeDefByteOrder]:
        raise NotImplementedError

    def test_byteorder_as(self):
        byteorders = [LittleEndian, BigEndian, NetworkEndian, NativeEndian, None]
        types = self.BYTEORDER_TYPEDEFS
        for byteorder in byteorders:
            for t in types:
                new_t = byteorder_as(t, byteorder)
                assert byteorder_of(new_t) == resolve_byteorder(byteorder), "'byteorder_of' not getting value set by 'byteorder_as'!"

    def test_byteorder_as_preserves_type(self):
        # A new types should be returned by byteorder_as; unless byteorder does not change; then the same type `should` be returned
        byteorders = [LittleEndian, BigEndian, NetworkEndian, NativeEndian, None]
        types = self.BYTEORDER_TYPEDEFS
        for byteorder in byteorders:
            for t in types:
                src_byteorder = byteorder_of(t)
                new_t = byteorder_as(t, byteorder)
                if src_byteorder == resolve_byteorder(byteorder):
                    if new_t is not t:
                        warnings.warn(UserWarning(f"'{t.__class__}' should return the same instance if byteorder does not change!"))
                else:
                    assert new_t is not t, "`byteorder_as` should not alter input `type-object`"

    def test_byteorder_as_equality(self):
        byteorders = [LittleEndian, BigEndian, NetworkEndian, NativeEndian, None]
        types = self.BYTEORDER_TYPEDEFS
        for byteorder in byteorders:
            for t in types:
                src_byteorder = byteorder_of(t)
                new_t = byteorder_as(t, byteorder)
                redef_t = byteorder_as(new_t, src_byteorder)
                assert t == redef_t, "Same byteorder should preserve equality of object!"

    def test_byteorder_as_inequality(self):
        byteorders = [LittleEndian, BigEndian, NetworkEndian, NativeEndian, None]
        types = self.BYTEORDER_TYPEDEFS
        for byteorder in byteorders:
            for t in types:
                src_byteorder = byteorder_of(t)
                new_t = byteorder_as(t, byteorder)
                if src_byteorder != resolve_byteorder(byteorder):
                    assert t != new_t, "Differing byteorder should break equality of object!"
