from PyQt6.QtCore import (Qt,
                          QRectF,
                          QLineF,
                          QPointF,
                          pyqtSignal)

from PyQt6.QtGui import QPen, QColor
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsEllipseItem

from custom import EntityClass

class Anchor(QGraphicsObject):

    # Signals:
    sig_item_clicked = pyqtSignal(QPointF)

    # Default Attribute(s):
    class Attr:
        def __init__(self):
            self.dims = QLineF( 0, -40,  0,  64)
            self.rect = QRectF(-5, -40, 10, 104)

    # Default anchor style:
    class Style:
        pen_default = QPen(QColor(0x006d8f), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        background  = QColor(0xffffff)

    # Initializer:
    def __init__(self,
                 eclass: EntityClass,
                 parent: QGraphicsItem):

        # Initialize super-class:
        super().__init__(parent)

        # Attrib:
        self._attr   = self.Attr()
        self._style  = self.Style()
        self._stream = eclass

        # Initialize hint:
        self._hint = QGraphicsEllipseItem(QRectF(-2.5, -2.5, 5.0, 5.0), self)
        self._hint.setBrush(Qt.GlobalColor.green)
        self._hint.setPen(QColor(0x0))
        self._hint.hide()

        # Item-behaviour:
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)

    @property
    def line(self): return self._attr.dims

    # Event-handler for paint-event:
    def paint(self, painter, option, widget = ...):
        painter.setPen(self._style.pen_default)
        painter.drawLine(self._attr.dims)

    # Returns the anchor's stream:
    def stream(self):
        return self._stream

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

        self.sig_item_clicked.emit(QPointF(0, ypos))
        event.accept()  # Prevent event propagation

    # Adjust size:
    def resize(self, delta: int):
        self._attr.dims.setP2(self._attr.dims.p2() + QPointF(0, delta))  # Adjust the end point of the line
        self._attr.rect.setBottom(self._attr.rect.bottom() + delta)
        self.update()