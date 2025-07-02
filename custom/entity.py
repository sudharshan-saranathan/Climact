from enum import Enum

from PyQt6.QtCore   import Qt
from PyQt6.QtGui    import QColor

from .stream        import Stream

class EntityClass(Enum):
    INP = 0
    OUT = 1
    VAR = 2
    PAR = 3
    EQN = 4

class EntityState(Enum):
    TOTAL  = 0
    HIDDEN = 1
    ACTIVE = 2

# Class Entity: Data structure to represent real-world resource flows:
class Entity(Stream):

    # Initializer:
    def __init__(self):

        # Initialize super-class:
        super().__init__("Default", QColor(Qt.GlobalColor.darkGray))

        # Define properties:
        self._prop = dict({
            "eclass"    : EntityClass.PAR,
            "symbol"    : str(),
            "label"     : str(),
            "units"     : str(),
            "info"      : str(),
            "uid"       : str(),
            "value"     : str(),
            "sigma"     : str(),
            "minimum"   : str(),
            "maximum"   : str()
        })

    # Clone this entity and return a reference:
    def clone_into(self, copied, **kwargs):

        # Copy this entity's attribute(s):
        copied.symbol  = self.symbol    if 'exclude' in kwargs and "symbol" in kwargs.values() else copied.symbol
        copied.eclass  = self.eclass    if 'exclude' in kwargs and "eclass" in kwargs.values() else copied.eclass
        copied.info    = self.info
        copied.units   = self.units
        copied.strid   = self.strid
        copied.value   = self.value
        copied.sigma   = self.sigma
        copied.minimum = self.minimum
        copied.maximum = self.maximum

    # uid (datatype = str): Unique resource-identifier
    @property
    def uid(self)   -> str : return self._prop["uid"]

    @uid.setter
    def uid(self, uid: str):

        # Set UID:
        self._prop["uid"] = uid

    # Info (datatype = str): Description of the entity
    @property
    def info(self)  -> str : return self._prop["info"]

    @info.setter
    def info(self, info: str):  self._prop["info"] = info

    @property
    def label(self) -> str | None: return self._prop["label"]

    @label.setter
    def label(self, label: str):    self._prop["label"] = label

    @property
    def units(self) -> str: return self._units

    @units.setter
    def units(self, units: str):   self._units = units

    @property
    def eclass(self) -> EntityClass:
        return self._prop["eclass"]

    @eclass.setter
    def eclass(self, eclass: EntityClass):
        self._prop["eclass"] = eclass
        
    @property
    def symbol(self) -> str: return self._prop["symbol"]

    @symbol.setter
    def symbol(self, symbol: str): self._prop["symbol"] = symbol

    @property
    def value(self) -> str: return self._prop["value"]

    @value.setter
    def value(self, value: str):   self._prop["value"] = value

    @property
    def sigma(self) -> str: return self._prop["sigma"]

    @sigma.setter
    def sigma(self, sigma: str):

        # Set sigma:
        self._prop["sigma"] = sigma

    @property
    def minimum(self) -> str: return self._prop["minimum"]

    @minimum.setter
    def minimum(self, minimum: str):    self._prop["minimum"] = minimum

    @property
    def maximum(self) -> str: return self._prop["maximum"]

    @maximum.setter
    def maximum(self, maximum: str):    self._prop["maximum"] = maximum