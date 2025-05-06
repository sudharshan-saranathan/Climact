from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPalette
from PyQt6.QtWidgets import QWidget, QWidgetAction, QLabel, QHBoxLayout, QCheckBox

from core.util import random_hex

class Category:

    # Global list:
    Set = set()

    # Initializer:
    def __init__(self, _cname: str, _color: QColor):
        self._cname = _cname
        self._color = _color

    @property
    def cname(self) -> str: return self._cname

    @cname.setter
    def cname(self, value):
        if isinstance(value, str):
            self._cname = value

    @property
    def color(self) -> QColor:  return self._color

    @color.setter
    def color(self, _color):

        if _color is None:
            return

        try:
            self._color = QColor(_color)

        except RuntimeError as exception:
            print(f"Invalid color: {_color} ({exception})")

    @staticmethod
    def find_category_by_label(category: str, create_new: bool = True):

        # If category is empty, select default:
        category = "Default" if category == "" else category

        # Find category by name and return:
        for _category in Category.Set:
            label =  category
            match = _category.cname
            if label == match:
                return _category

        # If it doesn't exist, create new category with a random color:
        if  create_new:
            _new_category = Category(category, QColor(random_hex()))
            Category.Set.add(_new_category)
            return _new_category

        return None

class CategoryLabel(QLabel):

    # Signals:
    sig_label_hovered = pyqtSignal()

    # Initializer:
    def __init__(self, _label, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(_label, parent)

        # Customize:
        self.setIndent(4)
        self.setMouseTracking(True)
        self.setStyleSheet("QLabel {border-radius: 6px; color: black;}")

    def enterEvent(self, event):
        self.setStyleSheet("QLabel {background: #e0e0e0; color: #187795;}")

    def leaveEvent(self, a0):
        self.setStyleSheet("QLabel {background: transparent; color: black;}")

class CategoryAction(QWidgetAction):

    # Initializer:
    def __init__(self, _category: Category, set_selected: bool):

        # Initialize base-class:
        super().__init__(None)

        # Colored indicator:
        size = 16
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(_category.color)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(2, 2, size-4, size-4)
        painter.end()

        # Containers:
        text_label = CategoryLabel(_category.cname, None)
        text_label.setObjectName("Action-label")

        if set_selected:
            text_font = text_label.font()
            text_font.setBold(True)
            text_font.setItalic(True)
            text_label.setFont(text_font)

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedWidth(16)
        icon_label.setObjectName("Color-indicator")

        # Widget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Layout items:
        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        # Add widget to action:
        self.setDefaultWidget(widget)

    def action_label(self):
        text_label = self.defaultWidget().findChild(QLabel, "Action-label")
        if isinstance(text_label, QLabel):
            return text_label.text()

        return None