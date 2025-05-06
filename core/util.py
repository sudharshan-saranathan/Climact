from PyQt6.QtGui    import *
from PyQt6.QtCore   import *

import string
import random

# Function to parse a qss-stylesheet:
def qss(filename: str) -> str:
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

def random_hex():
    return "#{:06x}".format(random.randint(0, 0xffffff))

def anti_color(color: QColor):
    """
    Returns a contrasting color (either white or black) based on the luminance of the input color
    :param color: The color against which the contrasting color is sought.
    :return: Black if the input color is light, otherwise white.
    """
    def normalize(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    luminance = (0.2126 * normalize(color.red()) +
                 0.7152 * normalize(color.green()) +
                 0.0722 * normalize(color.blue()))

    return QColor(0x000000) if luminance > 0.5 else QColor(0xffffff)

def str_to_float(arg: str):
    try:                return float(arg)
    except ValueError:  return None