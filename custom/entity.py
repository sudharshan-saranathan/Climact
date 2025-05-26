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
            "uid"       : str(),
            "info"      : str(),
            "label"     : str(),
            "units"     : str(),
            "eclass"    : None,
            "symbol"    : str(),
            "value"     : str(),
            "sigma"     : str(),
            "minimum"   : str(),
            "maximum"   : str()
        })

    # Clone this entity and return a reference:
    def clone_into(self, _copied):

        # Copy this entity's attribute(s):
        _copied.symbol  = self.symbol
        _copied.eclass  = self.eclass
        _copied.info    = self.info
        _copied.units   = self.units
        _copied.strid   = self.strid
        _copied.color   = self.color
        _copied.value   = self.value
        _copied.sigma   = self.sigma
        _copied.minimum = self.minimum
        _copied.maximum = self.maximum

    # uid (datatype = str): Unique resource-identifier
    @property
    def uid(self)   -> str : return self._prop["uid"]

    @uid.setter
    def uid(self, _uid: str):

        # Validate input-type:
        if not isinstance(_uid, str):
            raise TypeError("Expected str")

        # Set UID:
        self._prop["uid"] = _uid

    # Info (datatype = str): Description of the entity
    @property
    def info(self)  -> str : return self._prop["info"]

    @info.setter
    def info(self, _info: str):

        # Validate input-type:
        if  not isinstance(_info, str):
            raise TypeError("Expected str")

        # Set UID:
        self._prop["info"] = _info

    @property
    def label(self) -> str | None: return self._prop["label"]

    @label.setter
    def label(self, _label: str):

        # Validate input-type:
        if  not isinstance(_label, str):
            raise TypeError("Expected str")

        # Set label:
        self._prop["label"] = _label

    @property
    def units(self) -> str: return self._prop["units"]

    @units.setter
    def units(self, _units: str):

        # Validate input-type:
        if  not isinstance(_units, str):
            raise TypeError("Expected str")

        # Set units:
        self._prop["units"] = _units

    @property
    def eclass(self) -> EntityClass | None:
        _name = self._prop["eclass"]
        return EntityClass[_name] if _name else None

    @eclass.setter
    def eclass(self, _eclass: EntityClass):

        # Validate input-type:
        if  not isinstance(_eclass, EntityClass):
            raise TypeError("Expected argument of type `EntityClass`")

        # Set eclass:
        self._prop["eclass"] = _eclass.name
        
    @property
    def symbol(self) -> str: return self._prop["symbol"]

    @symbol.setter
    def symbol(self, _symbol: str):

        # Validate input-type:
        if not isinstance(_symbol, str):
            raise TypeError("Expected str")

        # Set symbol:
        self._prop["symbol"] = _symbol

    @property
    def value(self) -> str: return self._prop["value"]

    @value.setter
    def value(self, _value: str):

        # Validate input-type:
        if not isinstance(_value, str):
            raise TypeError("Expected argument of type `str`")

        # Set value:
        self._prop["value"] = _value

    @property
    def sigma(self) -> str: return self._prop["sigma"]

    @sigma.setter
    def sigma(self, _sigma: str):

        # Validate input-type:
        if not isinstance(_sigma, str):
            raise TypeError("Expected argument of type `str`")

        # Set sigma:
        self._prop["sigma"] = _sigma

    @property
    def minimum(self) -> str: return self._prop["minimum"]

    @minimum.setter
    def minimum(self, _minimum: str):

        # Validate input-type:
        if not isinstance(_minimum, str):
            raise TypeError("Expected argument of type `str`")

        # Set minimum:
        self._prop["minimum"] = _minimum

    @property
    def maximum(self) -> str: return self._prop["maximum"]

    @maximum.setter
    def maximum(self, _maximum: str):

        # Validate input-type:
        if not isinstance(_maximum, str):
            raise TypeError("Expected argument of type `str`")

        # Set maximum:
        self._prop["maximum"] = _maximum