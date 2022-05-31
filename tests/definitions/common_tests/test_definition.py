import warnings
from typing import List, Any

from definitions.util import classproperty
from structlib.packing.protocols import align_of, align_as


# AVOID using test as prefix
class DefinitionTests:

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

    @classproperty
    def DEFINITION(self) -> Any:
        raise NotImplementedError

    def test_definition_equality(self):
        _DEF = self.DEFINITION
        if _DEF is not None:
            assert self.CLS == _DEF
            assert self.INST == _DEF
        assert self.CLS == self.INST
        assert self.CLS_LE == self.INST_LE
        assert self.CLS_BE == self.INST_BE

    def test_definition_inequality(self):
        assert self.CLS_LE != self.CLS_BE
        assert self.CLS_LE != self.INST_BE
        assert self.INST_LE != self.CLS_BE
        assert self.INST_LE != self.INST_BE
