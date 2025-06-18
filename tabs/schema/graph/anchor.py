"""
anchor.py
"""

from PyQt6.QtCore import (Qt,
                          QRectF,
                          QLineF,
                          QPointF,
                          pyqtSignal)
from PyQt6.QtGui import (
    QPen,
    QColor
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsEllipseItem
)

import types
import logging
import dataclasses

from enum import Enum
from custom import EntityRole

class Anchor(QGraphicsObject):
    """
    A custom `QGraphicsObject` in the shape of a vertical line that anchors `handles` (see handle.py) to the node.
    """
    # Signals:
    sig_item_clicked = pyqtSignal(QPointF)

    # Constants:
    constants = {
        EntityRole.INP: QPointF(-95, 0),
        EntityRole.OUT: QPointF( 95, 0)
    }

    # Initializer:
    def __init__(self,
                 role:   EntityRole,        # `EntityRole` of the anchor (see custom/entity.py)
                 parent: QGraphicsItem):    # `QGraphicsItem` parent

        # Initialize super-class:
        super().__init__(parent)
        super().setAcceptHoverEvents(True)
        super().setPos(self.constants[role])        # Set position based on the role (input or output).

        # Attribute(s):
        self._attr = types.SimpleNamespace(
            dims = QLineF( 0, -40,  0,  64),        # Vertical line from (-40, 0) to (68, 0)
            rect = QRectF(-5, -40, 10, 108),        # Rectangle bounding the anchor
            role = role
        )
        self._style = types.SimpleNamespace(
            pen_default = QPen(QColor(0x006d8f), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap),
            background  = QColor(0xffffff)
        )

        # Initialize hint:
        self._hint = QGraphicsEllipseItem(QRectF(-2.5, -2.5, 5.0, 5.0), self)
        self._hint.setBrush(0xcfffb3)
        self._hint.setPen(0x0)
        self._hint.hide()

    # Method required to be reimplemented:
    def boundingRect(self):
        """
        Returns the bounding rectangle of the anchor.
        :return: QRectF
        """
        return self._attr.rect

    # Event-handler for paint-event:
    def paint(self, painter, option, widget = ...):
        """
        Paints the anchor using the painter provided.
        :param painter:
        :param option:
        :param widget:
        :return:
        """
        painter.setPen(self._style.pen_default)
        painter.drawLine(self._attr.dims)

    # Displays a handle-hint on mouse-over:
    def hoverEnterEvent(self, event):
        """
        When the mouse hovers over the anchor, a handle-hint is displayed at the cursor position.
        :param event:
        """
        super().hoverEnterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hint.setPos(0, event.pos().y())
        self._hint.show()

    # Moves handle-hint with the cursor:
    def hoverMoveEvent(self, event):
        """
        When the mouse moves over the anchor, the handle-hint is updated to follow the cursor's vertical position.
        :param event:
        """
        super().hoverMoveEvent(event)
        self._hint.setPos(0, event.pos().y())

    # Hides the handle-hint on hover-leave:
    def hoverLeaveEvent(self, event):
        """
        When the mouse leaves the anchor, the handle-hint is made invisible.
        :param event:
        """
        super().hoverLeaveEvent(event)
        self.unsetCursor()
        self._hint.hide()

    # Event-handler for mouse-clicks:
    def mousePressEvent(self, event):
        """
        Handles mouse-press events on the anchor. When the left mouse button is pressed, it emits a signal with the
        y-coordinate of the click.
        :param event:
        """
        super().mousePressEvent(event)
        if event.isAccepted() or event.button() != Qt.MouseButton.LeftButton:
            return

        xpos = event.pos().x()                          # Unused coordinate.
        ypos = event.pos().y()                          # Y-coordinate of the click (in anchor's coordinate system).

        self.sig_item_clicked.emit(QPointF(0, ypos))    # Emit the y-coordinate of the click as a signal.
        event.accept()                                  # Without this, the click event will propagate to the parent.

    # Adjust size:
    def resize(self, delta: int):
        """
        Resizes the anchor and adjusts its vertical dimensions.
        :param delta:
        """
        self._attr.dims.setP2(self._attr.dims.p2() + QPointF(0, delta))     # Adjust dimensions.
        self._attr.rect.setBottom(self._attr.rect.bottom() + delta)         # Adjust the bottom of the bounding rectangle.
        self.update()

    @property
    def line(self):
        """
        Returns a `QLineF` representing the anchor's vertical line.
        :return: QLineF
        """
        return self._attr.dims

    @property
    def role(self) -> EntityRole:
        """
        Returns the `EntityRole` of the anchor.
        :return: EntityRole
        """
        return self._attr.role