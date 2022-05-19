from typing import Tuple, Any

from structlib.definitions.common import PrimitiveStructMixin
from structlib.protocols import size_of, align_of
from structlib.protocols_old import PackAndSizeLike


class Array(PrimitiveStructMixin):
    """
    An 'Array' only allows fixed-sized types, mimicking C++
    """

    def __init__(self, args: int, data_type: PackAndSizeLike):
        # TODO how to align arrays?!
        #   Is it per element? Or to the first pointer?
        #       Unrelated; my understanding of size_of seems to be wrong `https://stackoverflow.com/questions/44023546/c-alignment-and-arrays`
        # FOR NOW, align to size and avoid the issue altogether (or the align specified)
        size = size_of(data_type)
        try:
            align = align_of(data_type)
        except AttributeError:  # TODO better align_of
            align = size

        PrimitiveStructMixin.__init__(self, size=args * size, align_as=align, args=args)
        self._data_type = data_type

    def _pack(self, *args: Any) -> bytes:
        s = size_of(self._data_type)
        buf = bytearray(self._size_)
        for i, d in enumerate(args):
            buf[i * s:(i + 1) * s] = self._data_type.pack(*d)
        return buf

    def _unpack(self, buffer: bytes) -> Tuple[Any, ...]:
        s = size_of(self._data_type)
        results = []
        for i in range(self._args_()):
            results.append(self._data_type.unpack(buffer[i * s:(i + 1) * s]))
        return tuple(results)
