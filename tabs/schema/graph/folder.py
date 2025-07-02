import qtawesome as qta

from util import load_svg
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsTextItem,
    QGraphicsItemGroup
)

from tabs.schema.graph.node import Node
from tabs.schema.graph.terminal import StreamTerminal
from custom import Label

# Node default configuration:
groupDefaults = {
    "guid"          : str(),
    "name"          : "Group",
    "spos"          : QPointF(0, 0),
    "rect"          : QRectF(-100, -75, 200, 120),
    "normal-border" : QPen(QColor(0x000000), 2.0),
    "select-border" : QPen(QColor(0xf99c39), 2.0),
    "background"    : QColor(0xede7e3),
}

# Class Folder:
class Folder(QGraphicsObject):

    # Constructor:
    def __init__(self, items: list, parent: QGraphicsItem | None = None):

        super().__init__(parent)
        super().setAcceptHoverEvents(True)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Rectangle:
        self._rect = groupDefaults["rect"]
        self._name = Label(self, "Group", width=150, editable = True, align=Qt.AlignmentFlag.AlignCenter)
        self._name.setPos(-75, -72)
        self._fill = QColor(0x078B9C)

        self._nodeCount = 0
        self._termCount = 0
        for item in items:
            if isinstance(item, Node):
                self._nodeCount += 1

            if isinstance(item, StreamTerminal):
                self._termCount += 1

    def boundingRect(self):
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):

        pen = groupDefaults["normal-border"] if not self.isSelected() else groupDefaults["select-border"]
        brs = groupDefaults["background"]

        painter.setPen  (pen)
        painter.setBrush(brs)
        painter.drawRoundedRect(groupDefaults["rect"], 8, 8)

        pen = QPen(Qt.GlobalColor.black, 1.0)
        painter.setPen(pen)
        painter.drawLine(QPointF(-98, -48), QPointF(98, -48))

        rect = QRectF(-12, -12, 24, 24)
        painter.setBrush(self._fill)
        painter.drawRoundedRect(-80, -28, 24, 24, 6, 6)
        painter.drawRoundedRect(-80, 0, 24, 24, 6, 6)
        painter.drawRoundedRect(-50, 0, 24, 24, 6, 6)
        painter.drawEllipse(-50, -28, 24, 24)

        painter.drawText(0, -28, 80, 24, Qt.AlignmentFlag.AlignRight, f"Nodes: {self._nodeCount}")
        painter.drawText(0, 0, 80, 24, Qt.AlignmentFlag.AlignRight, f"Terminals: {self._termCount}")

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.unsetCursor()