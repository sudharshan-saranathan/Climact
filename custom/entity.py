"""
entity.py
"""
import dataclasses
from enum import Enum

import numpy as np
import pydantic

from util import validator

# Enumeration of entity-states:
class EntityState(Enum):
    """
    An enumeration to represent the state of an entity.
    """
    ACTIVE = 0
    HIDDEN = 1
    BOTH   = 2

# Enumeration of entity-roles:
class EntityRole(Enum):
    """
    Enumeration to distinguish between input and output entities.
    """
    INP = 0,
    OUT = 1,

# Enumeration of entity-classes:
class EntityClass(Enum):
    """
    Enumeration to represent the class of an entity.
    """
    VAR = 0,  # Variable
    PAR = 1,  # Parameter
    EQN = 2,  # Equation

# Enumeration of entity-evolution models:
class Evolution(Enum):
    """
    Enumeration to denote the functional form of the entity's time-evolution.
    """
    CONSTANT   = 0     # x(t) = c
    LINEAR     = 1     # x(t) = a + bt
    SIGMOID    = 2     # x(t) = a / (1 + exp(-b * (t - c))) + d
    POLYNOMIAL = 3     # x(t) = a + bt + ct^2 + dt^3

# Class `Entity`:
class Entity:
    """
    A class denoting a dynamic entity (variables or parameters) in the Climact simulation platform.
    """
    # Metadata for the entity:
    class Metadata(pydantic.BaseModel):
        """
        Metadata for an entity, including symbol, label, info, and units.
        """
        eclass: EntityClass = EntityClass.PAR
        symbol: str = ""
        label:  str = ""
        units:  str = ""
        strid:  str = "Default"
        info:   str = ""

    # Dynamic attributes:
    class Dynamic(pydantic.BaseModel):
        """
        Metadata for the evolution of an entity, including its type and parameters.
        """
        model:   Evolution = Evolution.CONSTANT     # Evolution model (default: CONSTANT)
        value:   float = np.nan                     # Value of the entity
        sigma:   float = np.nan                     # Standard deviation (for Gaussian models)
        maximum: float = np.nan                     # Maximum value (for bounded models)
        minimum: float = np.nan                     # Minimum value (for bounded models)

        @pydantic.validator("value", "sigma", "maximum", "minimum", pre=True)
        def coerce_to_nan(cls, value):
            """
            Converts empty strings to NaN for numeric fields.
            :param value: The value to validate.
            :return: float or np.nan
            """
            try:                                return float(value)
            except (ValueError, TypeError):     return np.nan

    # Boundary conditions:
    class Boundary(pydantic.BaseModel):
        """
        Boundary conditions for an entity, including initial and final values.
        """
        start_time: float = np.nan
        final_time: float = np.nan
        delta_time: float = np.nan

    def __init__(self,
                 eclass: EntityClass,
                 symbol: str,
                 strid: str,
                 **kwargs):
        """
        Initializes an empty entity.
        """
        # For MRO compatibility:
        super().__init__(**kwargs)

        # Metadata:
        self._meta = self.Metadata(
            eclass = eclass,
            symbol = symbol,
            strid  = strid,
        )
        self._data = self.Dynamic()
        self._bounds = self.Boundary()

    # TODO: Implement user-defined methods:
    #

    def evaluate(self, t: float) -> float:
        """
        Evaluates the entity's value at time t based on its evolution model and parameters.
        :param t: Time at which to evaluate the function.
        :return: Evaluated value at time t.
        """
        model = self._data.model
        val   = self._data.value
        vmax  = self._data.maximum
        vmin  = self._data.minimum
        sigma = self._data.sigma

        if  model == Evolution.CONSTANT:
            return val
        elif model == Evolution.LINEAR:
            return val + sigma * t
        elif model == Evolution.SIGMOID:
            return val / (1.0 + np.exp(-sigma * (t - vmax)))  # val = a, sigma = b, vmin = c
        elif model == Evolution.POLYNOMIAL:
            return val + sigma * t + vmin * t**2 + vmin * t**3  # val = a, sigma = b, vmin = c, vmax = d
        else:
            raise NotImplementedError(f"Model '{model}' is not supported.")

    @validator
    def import_data(self, entity, exclude: str | list | None = None):
        """
        Imports data from another entity instance into this entity.
        :param entity: The entity instance from which to import data.
        :param exclude: A list of attributes to exclude from the import.
        """

        if    isinstance(exclude, str) : exclude = {exclude}
        elif  isinstance(exclude, list): exclude = set(exclude)
        else: exclude = set()

        # Copy metadata properties
        if 'symbol' not in exclude:     self._meta.symbol = entity.symbol
        if 'label'  not in exclude:     self._meta.label  = entity.label
        if 'info'   not in exclude:     self._meta.info   = entity.info
        if 'units'  not in exclude:     self._meta.units  = entity.units
        if 'strid'  not in exclude:     self._meta.strid  = entity.strid

        # Copy dynamic data properties
        if 'model'   not in exclude:    self._data.model   = entity.model
        if 'value'   not in exclude:    self._data.value   = entity.value
        if 'sigma'   not in exclude:    self._data.sigma   = entity.sigma
        if 'maximum' not in exclude:    self._data.maximum = entity.maximum
        if 'minimum' not in exclude:    self._data.minimum = entity.minimum

        # Copy boundary properties
        if 'start_time' not in exclude: self._bounds.start_time = entity.start_time
        if 'final_time' not in exclude: self._bounds.final_time = entity.final_time
        if 'delta_time' not in exclude: self._bounds.delta_time = entity.delta_time

    @property
    def meta(self) -> Metadata:
        """
        Returns the metadata of the entity.
        :return: Metadata
        """
        return self._meta

    @property
    def data(self) -> Dynamic:
        """
        Returns the numeric data of the entity.
        :return: Numeric
        """
        return self._data

    @property
    def bounds(self) -> Boundary:
        """
        Returns the boundary conditions of the entity.
        :return: Boundary
        """
        return self._bounds

    @property
    def eclass(self) -> EntityClass:
        """
        Returns the class of the entity.
        :return: EntityClass
        """
        return self._meta.eclass

    @property
    def symbol(self) -> str:
        """
        Returns the symbol of the entity.
        :return: str
        """
        return self._meta.symbol

    @property
    def strid(self) -> str:
        """
        Returns the strid (Stream ID) of the entity.
        :return: str
        """
        return self._meta.strid

    @property
    def label(self) -> str:
        """
        Returns the label of the entity.
        :return: str
        """
        return self._meta.label

    @property
    def info(self) -> str:
        """
        Returns the info of the entity.
        :return: str
        """
        return self._meta.info

    @property
    def units(self) -> str:
        """
        Returns the units of the entity.
        :return: str
        """
        return self._meta.units

    @property
    def model(self) -> Evolution:
        """
        Returns the evolution model of the entity.
        :return: Evolution
        """
        return self._data.model

    @property
    def coeff(self) -> list:
        """
        Returns the coefficients of the evolution model.
        :return: list
        """
        return self._data.model[1:]

    @property
    def value(self) -> float:
        """
        Returns the current value of the entity.
        :return: float
        """
        return self._data.value

    @property
    def sigma(self) -> float:
        """
        Returns the standard deviation of the entity.
        :return: float
        """
        return self._data.sigma

    @property
    def maximum(self) -> float:
        """
        Returns the maximum value of the entity.
        :return: float
        """
        return self._data.maximum

    @property
    def minimum(self) -> float:
        """
        Returns the minimum value of the entity.
        :return: float
        """
        return self._data.minimum

    @property
    def start_time(self) -> float:
        """
        Returns the start time of the entity.
        :return: float
        """
        return self._bounds.start_time

    @property
    def final_time(self) -> float:
        """
        Returns the final time of the entity.
        :return: float
        """
        return self._bounds.final_time

    @property
    def delta_time(self) -> float:
        """
        Returns the delta time of the entity.
        :return: float
        """
        return self._bounds.delta_time

    @symbol.setter
    @validator
    def symbol(self, value: str):
        """
        Sets the symbol of the entity.
        :param value: The new symbol for the entity.
        """
        self._meta.symbol = value

    @eclass.setter
    @validator
    def eclass(self, value: EntityClass):
        """
        Sets the class of the entity.
        :param value: The new class for the entity.
        """
        self._meta.eclass = value

    @strid.setter
    @validator
    def strid(self, value: str):
        """
        Sets the strid of the entity.
        :param value: The new strid for the entity.
        """
        self._meta.strid = value

    @label.setter
    @validator
    def label(self, value: str):
        """
        Sets the label of the entity.
        :param value: The new label for the entity.
        """
        self._meta.label = value

    @info.setter
    @validator
    def info(self, value: str):
        """
        Sets the info of the entity.
        :param value: The new info for the entity.
        """
        self._meta.info = value

    @units.setter
    @validator
    def units(self, value: str):
        """
        Sets the units of the entity.
        :param value: The new units for the entity.
        """
        self._meta.units = value

    @model.setter
    @validator
    def model(self, value):
        """
        Sets the evolution model of the entity.
        :param value: The new evolution model for the entity.
        """
        self._data.model = Evolution(value)

    @value.setter
    @validator
    def value(self, value: float):
        """
        Sets the current value of the entity.
        :param value: The new value for the entity.
        """
        self._data.value = value

    @model.setter
    @validator
    def model(self, value: Evolution):
        """
        Sets the evolution model of the entity.
        :param value: The new evolution model for the entity.
        """
        self._data.model = value

    @sigma.setter
    @validator
    def sigma(self, value: float):
        """
        Sets the standard deviation of the entity.
        :param value: The new standard deviation for the entity.
        """
        self._data.sigma = value

    @maximum.setter
    @validator
    def maximum(self, value: float):
        """
        Sets the maximum value of the entity.
        :param value: The new maximum value for the entity.
        """
        self._data.maximum = value

    @minimum.setter
    @validator
    def minimum(self, value: float):
        """
        Sets the minimum value of the entity.
        :param value: The new minimum value for the entity.
        """
        self._data.minimum = value

    @start_time.setter
    @validator
    def start_time(self, value: float):
        """
        Sets the start time of the entity.
        :param value: The new start time for the entity.
        """
        self._bounds.start_time = value

    @final_time.setter
    @validator
    def final_time(self, value: float):
        """
        Sets the final time of the entity.
        :param value: The new final time for the entity.
        """
        self._bounds.final_time = value

    @delta_time.setter
    @validator
    def delta_time(self, value: float):
        """
        Sets the delta time of the entity.
        :param value: The new delta time for the entity.
        """
        self._bounds.delta_time = value