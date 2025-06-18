"""
stream.py
"""

from PyQt6.QtCore import (
    Qt,
    pyqtSignal
)
from PyQt6.QtGui import (
    QPainter,
    QPixmap,
    QColor
)
from PyQt6.QtWidgets import (
    QWidgetAction,
    QWidget,
    QHBoxLayout,
    QLabel,
)

from util import validator

class StreamActionLabel(QLabel):
    """
    A custom QLabel for displaying stream actions in a menu.
    """
    # Signals:
    sig_label_hovered = pyqtSignal()

    # Class constructor:
    @validator
    def __init__(self, 
                 label: str,
                 select: bool,
                 parent: QWidget | None
                ):
        # If selected, make the label bold:
        label = f"<b>{label}</b>" if select else label

        # Initialize base-class:
        super().__init__(label, parent)

        # Customize:
        self.setIndent(4)
        self.setStyleSheet("QLabel {border-radius: 6px; color: black;}")

    def enterEvent(self, _event):
        """
        Handle the mouse entering the label area.
        :param _event:
        """
        self.setStyleSheet("QLabel {background: #e0e0e0; color: #187795;}")

    def leaveEvent(self, _event):
        """
        Handle the mouse leaving the label area.
        :param _event:
        :return:
        """
        self.setStyleSheet("QLabel {background: transparent; color: black;}")

class StreamMenuAction(QWidgetAction):
    """
    A custom QWidgetAction for displaying a stream in a menu with a colored indicator.
    """
    # Class constructor:
    @validator
    def __init__(self, 
                 strid: str,
                 color: QColor,
                 select: bool
                ):
        # Initialize base-class:
        super().__init__(None)

        # Colored indicator:
        size = 16
        pixmap = QPixmap(size, size)      # Empty pixmap
        pixmap.fill(QColor(0, 0, 0, 0))   # Fill with a transparent background

        # Draw colored circle:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(2, 2, size-4, size-4)
        painter.end()

        # Containers:
        self._icon_label = QLabel()
        self._icon_label.setPixmap(pixmap)
        self._icon_label.setFixedWidth(16)
        self._icon_label.setObjectName("Color-indicator")

        # Widget:
        widget = QWidget()
        widget.setFixedHeight(24)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Set text-label:
        self._text_label = StreamActionLabel(
            strid,
            select,
            None
        )

        # Layout items:
        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)

        # Add widget to action:
        self.setCheckable(True)
        self.setChecked(select)
        self.setDefaultWidget(widget)

    @property
    def label(self):
        """
        Returns the text label of the stream action.
        :return:
        """
        return self._text_label.text()
