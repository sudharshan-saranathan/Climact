"""
evolution.py
"""

import numpy as np
from util import validator
from enum import Enum

class EvolutionType(Enum):
    """
    Enum representing different types of evolution models.
    """
    CONSTANT  = "constant"
    LINEAR    = "linear"
    QUADRATIC = "quadratic"
    CUBIC     = "cubic"
    SIGMOID   = "sigmoid"

class Constant:
    """
    A class representing a constant value.
    """
    def __init__(self, value: float):
        """
        Initializes the Constant with a given value.

        :param value: The constant value.
        """

        self.value = value  # The constant value

    # Evaluates the constant at a given x value (returns the constant value).
    def value(self, x: float) -> float:
        """
        Evaluates the constant at a given x value.

        :param x: The x value (not used, as the constant does not depend on x).
        :return: The constant value.
        """

        return self.value

class Linear:
    """
    A class representing a linear model with a slope and intercept (y = mx + b).
    """
    def __init__(self, slope: float, inter: float):
        """
        Initializes the Linear model with the given slope and intercept.

        :param slope: The slope of the linear function.
        :param inter: The y-intercept of the linear function.
        """

        self.slope  = slope    # Slope (m)
        self.offset = inter    # Intercept (b)

    # Evaluates the linear model at a given x value.
    def value(self, x: float) -> float:
        """
        Evaluates the linear model at a given x value.

        :param x: The x value to evaluate the model at.
        :return: The y value corresponding to the linear model.
        """
        return self.slope * x + self.offset

class Cubic:
    """
    A class representing a cubic model with coefficients for x^3, x^2, x, and a constant term.
    """
    def __init__(self,
                 offset : float,
                 coeff_1: float,
                 coeff_2: float,
                 coeff_3: float):

        self.offset  = offset    # Constant term (a)
        self.coeff_1 = coeff_1   # Coefficient for x (b)
        self.coeff_2 = coeff_2   # Coefficient for x^2 (c)
        self.coeff_3 = coeff_3   # Coefficient for x^3 (d)

    # Evaluates the cubic model at a given x value.
    def value(self, x: float) -> float:
        """
        Evaluates the cubic model at a given x value.

        :param x: The x value to evaluate the model at.
        :return: The y value corresponding to the cubic model.
        """
        return (
                self.coeff_3 * x**3 +
                self.coeff_2 * x**2 +
                self.coeff_1 * x +
                self.offset
        )

class Sigmoid:
    """
    A class representing to compute the sum of multiple sigmoid functions.
    """
    @validator
    def __init__(self,
                 basel: float,
                 count: int,
                 slope: float,
                 zeros: list[float],
                 steps: list[float]):
        """
        Initializes the Sigmoid model with the given parameters.

        :param slope: The slope of the sigmoid function.
        :param basel: The intercept of the sigmoid function.
        :param zeros: List of zero points for each sigmoid function.
        :param steps: List of scaling factors for each sigmoid function.
        """

        # Validate argument(s):
        if (
            len(zeros) != len(steps) or
            len(zeros) != count
        ):
            raise ValueError("The length of zeros and steps must be the same.")

        self.count: int      = count     # Number of sigmoid steps
        self.slope: float    = slope     # The steepness of the sigmoid function
        self.basel: float    = basel     # Baseline value (intercept)
        self.zeros: np.array = zeros     # The x-positions of the sigmoid steps (numpy array)
        self.steps: np.array = steps     # The height of each sigmoid step (numpy array)

    def value(self, x: float) -> float:
        """
        Evaluates the sum of multiple sigmoid functions at a given x value.
        :param x:
        :return: The sum of the sigmoid functions evaluated at x.
        """

        result = 0.0
        for zero, step in zip(self.zeros, self.steps):
            result += (step / (1.0 + np.exp(-self.slope * (x - zero))))

        return result + self.basel
