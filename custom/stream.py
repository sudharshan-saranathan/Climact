from PyQt6.QtCore   import Qt
from PyQt6.QtGui    import QColor

from PyQt6.QtWidgets import (
    QWidgetAction,
    QWidget,
    QHBoxLayout,
    QLabel,
)

from PyQt6.QtGui  import QPainter, QPixmap
from PyQt6.QtCore import pyqtSignal

# Class Stream:
class Stream:

    # Instance initializer:
    def __init__(self, strid: str, color: QColor | Qt.GlobalColor, units: str | None = None):

        # Store stream-ID and color:
        self._strid = strid
        self._color = color
        self._units = units

        # Additional user-defined properties:
        self._prop = {}

    # Properties:
    @property # FlowStream-ID (datatype = str): A unique identifier
    def strid(self) -> str: return self._strid

    @property # Color (datatype = QColor): Color of the stream
    def color(self) -> QColor: return QColor(self._color)

    @property # Units (datatype = str): Units of the stream
    def units(self) -> str | None:  return self._units

    @color.setter # Color setter
    def color(self, color):
        # Set color:
        self._color = color

    @strid.setter # String-ID setter
    def strid(self, strid):
        # Set string ID:
        self._strid = strid

    @units.setter # Units setter
    def units(self, units: str | None):
        # Set units:
        self._units = units

class StreamActionLabel(QLabel):

    # Signals:
    sig_label_hovered = pyqtSignal()

    # Initializer:
    def __init__(self,
                 label: str,
                 select: bool,
                 parent: QWidget | None
                 ):
        """
        Initialize a category label.
        """

        # If selected, make the label bold:
        label = f"<b>{label}</b>" if select else label

        # Initialize base-class:
        super().__init__(label, parent)

        # Customize:
        self.setIndent(4)
        self.setStyleSheet("QLabel {border-radius: 6px; color: black;}")

    def enterEvent(self, _event):   self.setStyleSheet("QLabel {background: #e0e0e0; color: #187795;}")

    def leaveEvent(self, _event):   self.setStyleSheet("QLabel {background: transparent; color: black;}")

class StreamMenuAction(QWidgetAction):

    # Initializer:
    def __init__(self,
                 stream: Stream,
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
        painter.setBrush(stream.color)
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
        self._text_label = StreamActionLabel(stream.strid, select, None)

        # Layout items:
        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)

        # Add widget to action:
        self.setCheckable(True)
        self.setChecked(select)
        self.setDefaultWidget(widget)

    @property
    def label(self):    return self._text_label.text()
