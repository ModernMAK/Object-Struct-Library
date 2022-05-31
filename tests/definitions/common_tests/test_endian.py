import warnings
from typing import Any

from structlib.byteorder import Endian, resolve_byteorder
from structlib.packing.protocols import endian_as, endian_of


# Stolen from
# https://stackoverflow.com/qstions/128573/using-property-on-classmethods/64738850#64738850
# We don't use @classmethod + @property to allow <= 3.9 support
class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


classproperty = ClassProperty  # Alias for decorator

# AVOID using test as prefix
class EndianTests:
    @classproperty
    def CLS(self) -> Any:
        raise NotImplementedError

    @classproperty
    def CLS_LE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def CLS_BE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST_LE(self) -> Any:
        raise NotImplementedError

    @classproperty
    def INST_BE(self) -> Any:
        raise NotImplementedError

    def test_endian_as(self):
        endians = [Endian.Little, Endian.Big, "little", "big", None]
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for endian in endians:
            for t in types:
                new_t = endian_as(t, endian)
                assert endian_of(new_t) == resolve_byteorder(endian), "'endian_of' not getting value set by 'endian_as'!"

    def test_endian_as_preserves_type(self):
        # A new types should be returned by endian_as; unless endian does not change; then the same type `should` be returned
        endians = [Endian.Little, Endian.Big, "little", "big", None]
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for endian in endians:
            for t in types:
                src_endian = endian_of(t)
                new_t = endian_as(t, endian)
                if src_endian == resolve_byteorder(endian):
                    if new_t is not t:
                        warnings.warn(UserWarning(f"'{t.__class__}' should return the same instance if endian does not change!"))
                else:
                    assert new_t is not t, "`endian_as` should not alter input `type-object`"

    def test_endian_as_equality(self):
        endians = [Endian.Little, Endian.Big, "little", "big", None]
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for endian in endians:
            for t in types:
                src_endian = endian_of(t)
                new_t = endian_as(t, endian)
                redef_t = endian_as(new_t, src_endian)
                assert t == redef_t, "Same endian should preserve equality of object!"

    def test_endian_as_inequality(self):
        endians = [Endian.Little, Endian.Big, "little", "big", None]
        types = [self.CLS, self.CLS_LE, self.CLS_BE, self.INST, self.INST_LE, self.INST_BE]
        for endian in endians:
            for t in types:
                src_endian = endian_of(t)
                new_t = endian_as(t, endian)
                if src_endian != resolve_byteorder(endian):
                    assert t != new_t, "Differing endian should break equality of object!"
