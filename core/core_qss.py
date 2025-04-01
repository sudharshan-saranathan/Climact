import random
import string

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen



class QSS:

    pen_default  = QPen(QColor(0x000000), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    pen_focused  = QPen(QColor(0xffa21f), 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

    @staticmethod
    def random_id(length: int = 6, prefix: str = ""):
        if not isinstance(length, int):
            return None

        if not isinstance(prefix, str):
            return None

        random_id = prefix + ''.join(random.choices(string.digits, k=length))
        return random_id


    @staticmethod
    def random_hex():
        return "#{:06x}".format(random.randint(0, 0xffffff))

    @staticmethod
    def anti_color(color: QColor):

        """Compute WCAG-compliant relative luminance."""
        def normalize(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        red, green, blue = color.red(), color.green(), color.blue()
        luminance = 0.2126 * normalize(red) + 0.7152 * normalize(green) + 0.0722 * normalize(blue)
        anticolor = QColor(QColor(0x000000) if luminance > 0.5 else QColor(0xffffff))

        return anticolor
