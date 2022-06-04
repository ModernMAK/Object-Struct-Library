import warnings
from typing import Any, List

from typedefs.util import classproperty


# AVOID using test as prefix
class DefinitionTests:
    @classproperty
    def EQUAL_DEFINITIONS(self) -> List[Any]:
        raise NotImplementedError

    @classproperty
    def INEQUAL_DEFINITIONS(self) -> List[Any]:
        raise NotImplementedError

    @classproperty
    def DEFINITION(self) -> Any:
        raise NotImplementedError

    def test_definition_equality(self):
        _DEF = self.DEFINITION
        if _DEF is not None:
            for _def in self.EQUAL_DEFINITIONS:
                assert _def == _DEF

    def test_definition_inequality(self):
        _DEF = self.DEFINITION
        if _DEF is not None:
            for _def in self.INEQUAL_DEFINITIONS:
                assert _def != _DEF
