from enum import Enum
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal
from PyQt6.QtGui  import QPen, QColor
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsEllipseItem

class Stream(Enum):
    INP = 1
    OUT = 2
    PAR = 3

class Anchor(QGraphicsObject):

    # Signals:
    sig_item_clicked = pyqtSignal(QPointF, bool)

    # Default Attribute(s):
    class Attr:
        type  = QGraphicsItem.UserType + 2
        def __init__(self):
            self.width = 4.0
            self.dims  = QLineF(  0, -60,  0,  90)
            self.rect  = QRectF(-20, -60, 40, 150)

    # Default anchor style:
    class Style:
        pen_default = QPen(QColor(0x006d8f), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        background  = QColor(0xffffff)

    def __init__(self, stream: Stream, parent: QGraphicsItem):
        super().__init__(parent)

        # Attrib:
        self._attr = self.Attr()
        self._styl = self.Style()
        self._strm = stream

        # Initialize hint:
        self._hint = QGraphicsEllipseItem(QRectF(-2.5, -2.5, 5.0, 5.0), self)
        self._hint.setBrush(QColor(Qt.GlobalColor.green))
        self._hint.setPen(QColor(0x0))
        self._hint.hide()

        # Item-behaviour:
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    # Returns the user-defined type:
    def type(self):
        return self._attr.type

    # Event-handler for paint-event:
    def paint(self, painter, option, widget = ...):
        painter.setPen(self._styl.pen_default)
        painter.drawLine(self._attr.dims)

    def stream(self):
        return self._strm

    # Returns bounding-rectangle:
    def boundingRect(self):
        return self._attr.rect

    # Displays a handle-hint on mouse-over:
    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hint.setPos(0, event.pos().y())
        self._hint.show()

    # Moves handle-hint with the cursor:
    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self._hint.setPos(0, event.pos().y())

    # Hides the handle-hint on hover-leave:
    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.unsetCursor()
        self._hint.hide()

    # Event-handler for mouse-clicks:
    def mousePressEvent(self, event):

        super().mousePressEvent(event)
        if event.isAccepted() or event.button() != Qt.MouseButton.LeftButton:
            return

        xpos = event.pos().x()
        ypos = event.pos().y()

        self.sig_item_clicked.emit(QPointF(0, ypos), True)
        event.accept()  # Prevent event propagation

    # Adjust size:
    def adjust(self, delta: float):
        self._attr.dims.setP2(self._attr.dims.p2() + QPointF(0, delta))  # Adjust the end point of the line
        self._attr.rect.setBottom(self._attr.rect.bottom() + delta)
        self.update()