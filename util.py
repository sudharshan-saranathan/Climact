from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor
from enum         import Enum

import string
import random
import inspect
import functools

from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from typing import (
    Type,
    Generic,
    TypeVar
)

# Parse a qss-stylesheet:
def read_qss(filename: str) -> str:
    """
    Parses a QSS stylesheet file and returns contents.
    :param filename: Path to the file as a string.
    :return: Contents of the file as a string.
    """

    if not isinstance(filename, str):
        raise TypeError("Expected argument of type str")

    with open("rss/style/macos.qss", "r") as file:
        _qss = file.read()

    return _qss

# Replace a substring in an expression and return transformed expression:
def replace(expression: str, old: str, new: str):
    """
    Replaces all occurrences of a word in a string that is delimited by ' '.
    :param expression: The string to be substituted.
    :param old: Word or symbol to be replaced
    :param new: Word or symbol to replace with.
    :return: Substituted string with all occurrences of `old` replaced by `new`
    """

    tokens = expression.split(' ')
    update = [new if token == old else token for token in tokens]
    return ' '.join(update)

# Generate a Unique Identifier (UID) of desired length and prefix:
def random_id(length: int = 4, prefix: str = ""):
    """
    Returns a random alphanumeric ID.
    :param length: Number of digits to use
    :param prefix: Prefix string added to the random ID
    :return: A random alphanumeric I, prefixed by `prefix`
    """

    if not isinstance(length, int) or not isinstance(prefix, str):
        return None

    return prefix + ''.join(random.choices(string.digits, k=length))

# Generate a random color:
def random_hex():   return "#{:06x}".format(random.randint(0, 0xffffff))

# Find the best contrasting color to any given color:
def anti_color(_color: QColor | Qt.GlobalColor | str):
    """
    Returns a contrasting color (white or black) based on the luminance of the input color.

    :param _color: The color against which the contrasting color is sought.
    :return: Black if the input color is light, otherwise white.
    """

    # Validate argument(s):
    try:
        _color = QColor(_color) 

    except TypeError:
        raise TypeError("Unable to convert argument to `QColor`")

    # Method to normalize color values:
    def normalize(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    # Compute luminance:
    luminance = (0.2126 * normalize(_color.red()) +
                 0.7152 * normalize(_color.green()) +
                 0.0722 * normalize(_color.blue()))

    # Return black or white based on luminance:
    return QColor(0x000000) if luminance > 0.5 else QColor(0xffffff)

# Convert string to float, return None if not possible:
def str_to_float(arg: str):
    """
    Converts a string to a float, returns None if not possible.
    
    Args:
        arg (str): The string to convert.

    Returns:
        float: The float value of the string, or None if not possible.
    """

    try:                return float(arg)
    except ValueError:  return None

# Scale an SVG to a specific width:
def load_svg(_file: str, _width: int):
    """
    Loads an SVG-icon and rescales it to a specific width.

    Args:
        _file (str): The path to the SVG-icon.
        _width (int): The width to rescale the SVG to.

    Returns:
        QGraphicsSvgItem: The rescaled SVG-icon.
    """

    # Validate argument(s):
    if (
        not isinstance(_file , str) or
        not isinstance(_width, int)
    ):
        return

    # Load SVG-icon and rescale:
    _svg = QGraphicsSvgItem(_file)
    _svg.setScale(float(_width / _svg.boundingRect().width()))  # Rescale the SVG

    return _svg

# Argument validator:
def ArgumentValidator(function):
    """
    A decorator to validate the arguments of a function, using the function's annotations
    """
    signature = inspect.signature(function)

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        """
        Validates the arguments of the function based on its annotations.
        :param args:
        :param kwargs:
        :return:
        """
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        for name, value in bound_args.arguments.items():
            expected_type = signature.parameters[name].annotation
            if (
                expected_type is not inspect.Parameter.empty and
                not isinstance(value, expected_type)
            ):
                raise TypeError(f"Argument '{name}' must be {expected_type}, got {type(value)} instead.")

        return function(*args, **kwargs)
    return wrapper

# Generic dictionary with runtime type-validation:
K = TypeVar('K')
class ValidatorDict(Generic[K], dict):
    """
    A generic TypedDict that allows for type hinting of dictionary keys and values.
    This is useful for defining structured data types in Python.
    """
    def __init__(self, key_type: Type[K], *args, **kwargs):
        self.key_type = key_type
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: K, value):
        if not isinstance(key, self.key_type):
            raise TypeError(f"Key must be of type {self.key_type.__name__}")
        super().__setitem__(key, value)