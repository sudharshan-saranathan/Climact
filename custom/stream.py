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
    def __init__(self, _strid: str, _color: QColor | Qt.GlobalColor):

        # Validate input types:
        if not isinstance(_strid, str):                         raise TypeError("Expected str")
        if not isinstance(_color, QColor | Qt.GlobalColor):     raise TypeError("Expected QColor or Qt.GlobalColor")

        # Store stream-ID and color:
        self._strid = _strid
        self._color = _color

    # Properties:
    @property # FlowStream-ID (datatype = str): A unique identifier
    def strid(self) -> str: return self._strid

    @property # Color (datatype = QColor): Color of the stream
    def color(self) -> QColor: return QColor(self._color)

    @color.setter # Color setter
    def color(self, _color):

        # Validate input-type:
        if not isinstance(_color, QColor | Qt.GlobalColor):
            raise TypeError("Expected QColor or Qt.GlobalColor")

        # Set color:
        self._color = _color

    @strid.setter # String-ID setter
    def strid(self, _strid):

        # Validate input:
        if not isinstance(_strid, str):
            raise TypeError("Expected str")

        # Set string ID:
        self._strid = _strid

class StreamActionLabel(QLabel):

    # Signals:
    sig_label_hovered = pyqtSignal()

    # Initializer:
    def __init__(self, 
                _label: str,
                _select: bool,
                _parent: QWidget | None
                ):
        """
        Initialize a category label.

        Args:
            _label (str): The label text.
            _parent (QWidget | None): The parent widget.
        """

        # If selected, make the label bold:
        _label = f"<b>{_label}</b>" if _select else _label

        # Initialize base-class:
        super().__init__(_label, _parent)

        # Customize:
        self.setIndent(4)
        self.setStyleSheet("QLabel {border-radius: 6px; color: black;}")

    def enterEvent(self, _event):   self.setStyleSheet("QLabel {background: #e0e0e0; color: #187795;}")

    def leaveEvent(self, _event):   self.setStyleSheet("QLabel {background: transparent; color: black;}")

class StreamMenuAction(QWidgetAction):

    # Initializer:
    def __init__(self, 
                _stream: Stream, 
                _select: bool
                ):
        """
        Initialize entry that goes into the `stream` sub-menu of a handle.

        Args:
            _stream (Stream): The stream to display in the action.
            _select (bool): Whether to select the action.
        """

        # Validate arguments:
        if not isinstance(_stream, Stream)  : raise TypeError("Expected argument `_stream` to be of type `Stream`")
        if not isinstance(_select, bool)    : raise TypeError("Expected argument `_select` to be of type `bool`")

        # Initialize base-class:
        super().__init__(None)

        # Colored indicator:
        size = 16
        pixmap = QPixmap(size, size)      # Empty pixmap
        pixmap.fill(QColor(0, 0, 0, 0))   # Fill with transparent background

        # Draw colored circle:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(_stream.color)
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
        self._text_label = StreamActionLabel(_stream.strid, _select, None)


        # Layout items:
        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)

        # Add widget to action:
        self.setCheckable(True)
        self.setChecked(_select)
        self.setDefaultWidget(widget)

    def label(self):    return self._text_label.text()
