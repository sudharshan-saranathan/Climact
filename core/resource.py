from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.category import Category

class Resource(Category):

    # Initializer:
    def __init__(self):

        # Initialize super-class:
        super().__init__("Default", QColor(Qt.GlobalColor.darkGray))

        # Define properties:
        self._prop = dict({
            "uid"       : None,
            "info"      : None,
            "label"     : None,
            "units"     : None,
            "symbol"    : None,
            "stream"    : None,
            "value"     : None,
            "sigma"     : None,
            "minimum"   : None,
            "maximum"   : None
        })

    @property
    def info(self)  -> str | None: return self._prop["info"]

    @info.setter
    def info(self, value):
        self._prop["info"] = value

    @property
    def label(self) -> str | None: return self._prop["label"]

    @label.setter
    def label(self, value):
        self._prop["label"] = value

    @property
    def units(self): return self._prop["units"]

    @units.setter
    def units(self, value): self._prop["units"] = value

    @property
    def symbol(self): return self._prop["symbol"]

    @symbol.setter
    def symbol(self, value): self._prop["symbol"] = value

    @property
    def stream(self): return self._prop["stream"]

    @stream.setter
    def stream(self, value): self._prop["stream"] = value

    @property
    def value(self): return self._prop["value"]

    @value.setter
    def value(self, val): self._prop["value"] = val

    @property
    def sigma(self): return self._prop["sigma"]

    @sigma.setter
    def sigma(self, val): self._prop["sigma"] = val

    @property
    def minimum(self): return self._prop["minimum"]

    @minimum.setter
    def minimum(self, val): self._prop["minimum"] = val

    @property
    def maximum(self): return self._prop["maximum"]

    @maximum.setter
    def maximum(self, val): self._prop["maximum"] = val