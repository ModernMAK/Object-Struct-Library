from typing import Callable, Type

from mypy.plugin import Plugin, AnalyzeTypeContext


class StructLibPlugin(Plugin):
    def get_type_analyze_hook(
        self, fullname: str
    ) -> Callable[[AnalyzeTypeContext], Type] | None:
        raise NotImplementedError


def plugin(version: str):
    return StructLibPlugin
