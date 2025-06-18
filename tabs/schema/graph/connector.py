"""
connector.py
"""
import numpy as np
import weakref
import qtawesome as qta

# PyQt6 Library:
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QPointF,
)
from PyQt6.QtGui import (
    QPen,
    QPainterPath, QColor
)
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
)

from dataclasses import dataclass, field
from typing import Optional

from custom import String
from util import validator, load_svg

from .handle import Handle

# Class Connector:
class Connector(QGraphicsObject):
    """
    A custom `QGraphicsObject` that represents a connection between two handles (input or output) in a graphical scene.
    """
    @dataclass
    class Metadata:
        """
        Metadata for the connector, including symbol and handles.
        """
        symbol: str = field(default_factory = str)  # Symbol representing the connector (default: empty string)
        origin: Optional[weakref.ref] = field(default = None)   # Origin handle (default: None)
        target: Optional[weakref.ref] = field(default = None)   # Target handle (default: None)

    @dataclass
    class Visual:
        """
        Visual attributes for the connector.
        """
        path: QPainterPath = field(default_factory = lambda: QPainterPath())                # Path for the connector
        pen_background: QPen = field(default_factory = lambda: QPen( Qt.GlobalColor.darkGray , 2.5))
        pen_foreground: QPen = field(default_factory = lambda: QPen( Qt.GlobalColor.lightGray, 2.0))

    @validator
    def __init__(self,
                 symbol: str = '',
                 origin: Handle | None = None,
                 target: Handle | None = None,
                 parent: QGraphicsItem | None = None):
        """
        Initializes the Connector with the origin and target handles.
        :param origin: The originating handle of the connection.
        :param target: The target handle of the connection.
        :param parent: The parent item in the graphics scene.
        """
        # Initialize the base class:
        super().__init__(parent)
        super().setZValue(-2)

        # Instantiate visual attributes:
        self._arrow_l = load_svg("rss/icons/direction.svg", 16)
        self._arrow_r = load_svg("rss/icons/direction.svg", 16)

        self._arrow_l.setParentItem(self)
        self._arrow_r.setParentItem(self)

        self._visual = self.Visual()    # The connector's visual attributes.
        self._meta   = self.Metadata(   # The connector's metadata.
            symbol = symbol,
            origin = None if origin is None else weakref.ref(origin),
            target = None if target is None else weakref.ref(target)
        )

        # If `origin` and `target` are provided, connect them:
        if (
            self._meta.origin and
            self._meta.target
        ):
            self._visual.pen_foreground.setColor(self._meta.origin().color)
            self._meta.origin().toggle_state(self, self._meta.target())
            self._meta.target().toggle_state(self, self._meta.origin())

            # Copy the origin's data into the target:
            self._meta.target().import_data(self._meta.origin(), exclude = ['symbol', 'color'])
            self._string = String(self, self._meta.symbol,
                                  align = Qt.AlignmentFlag.AlignCenter,
                                  editable = False, width = 40,
                                  bubble = True)

            # Draw the path:
            self.render(
                self._meta.origin().scenePos(),
                self._meta.target().scenePos()
            )

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the connector.
        :return: QRectF representing the bounding rectangle.
        """
        return self._visual.path.boundingRect()

    def paint(self, painter, option, widget=None):
        """
        Paints the connector using the provided painter.
        :param painter:
        :param option:
        :param widget:
        :return:
        """
        # First pass, paint with the thicker black pen:
        painter.setPen(self._visual.pen_background)
        painter.drawPath(self._visual.path)

        # Second pass, paint with the thinner pen:
        painter.setPen(self._visual.pen_foreground)
        painter.drawPath(self._visual.path)

    #
    #
    #

    @validator
    def render(self,
               opos: QPointF | None = None,
               tpos: QPointF | None = None):
        """
        Computes the path between the origin and target handles.
        :param opos: Origin position of the handle.
        :param tpos: Target position of the handle.
        """

        # If origin and target exist, argument-positions will be overridden:
        if self._meta.origin: opos = self._meta.origin().scenePos()
        if self._meta.target: tpos = self._meta.target().scenePos()

        # Emit geometry-change signal (needed to render correctly):
        self.prepareGeometryChange()
        self._visual.path.clear()
        self._visual.path = self.hexagonal(opos, tpos)

        # Show arrows:
        self._arrow_l.show()
        self._arrow_r.show()

        if hasattr(self, '_string'):
            # Update the string position:
            self._string.setPos(
                0.5 * (opos.x() + tpos.x()) - self._string.textWidth() / 2,
                0.5 * (opos.y() + tpos.y()) - self._string.boundingRect().height() / 2
            )

    @validator
    def reset(self):
        """
        Resets the connector's path to an empty state.
        """

        # Emit geometry-change signal (needed to render correctly):
        self.prepareGeometryChange()
        self._arrow_l.hide()
        self._arrow_r.hide()
        self._visual.path.clear()

    # ------------------------------------------------------------------------------------------------------------------
    # Path geometries
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # rectilinear()
    # hexagonal()
    # bezier()
    # ------------------------------------------------------------------------------------------------------------------

    @validator
    def rectilinear(self, opos: QPointF, tpos: QPointF):
        """
        Draws a rectilinear path between the origin and target handles.
        """

        xm = 0.5 * (opos.x() + tpos.x())
        ym = 0.5 * (opos.y() + tpos.y())

        path = QPainterPath()
        path.moveTo(opos)
        path.lineTo(xm, opos.y())
        path.lineTo(xm, tpos.y())
        path.lineTo(tpos)

        return path

    @validator
    def hexagonal(self, opos: QPointF, tpos: QPointF):
        """
        Draws a hexagonal path between the origin and target handles.
        """

        t  = np.pi / 6.0  if tpos.y() > opos.y() else 5 * np.pi / 6.0
        xm = 0.50 * (opos.x() + tpos.x())
        xd = np.tan(t) * (tpos.y() - opos.y()) / 2.0
        r  = min(0.50 * xd, 5)

        path = QPainterPath()
        path.moveTo(opos)

        self._arrow_l .setPos((opos.x() + xm - xd) / 2.0 - 8, opos.y() - 8)
        self._arrow_r.setPos((tpos.x() + xm + xd) / 2.0 - 8, tpos.y() - 8)

        # If the origin is to the left of the target, draw the path accordingly:
        if  opos.x() < tpos.x():
            path.lineTo(xm - xd - r, opos.y())
            path.quadTo(xm - xd, opos.y(), xm - xd + r * np.sin(t), opos.y() + r * np.cos(t))
            path.lineTo(xm + xd - r * np.sin(t), tpos.y() - r * np.cos(t))
            path.quadTo(xm + xd, tpos.y(), xm + xd + r, tpos.y())

        else:
            path.lineTo(xm + xd + r, opos.y())
            path.quadTo(xm + xd, opos.y(), xm + xd - r * np.sin(t), opos.y() + r * np.cos(t))
            path.lineTo(xm - xd + r * np.sin(t), tpos.y() - r * np.cos(t))
            path.quadTo(xm - xd, tpos.y(), xm - xd - r, tpos.y())

        path.lineTo(tpos)
        return path

    #
    #
    #

    @property
    def symbol(self) -> str:
        """
        Returns the symbol associated with the connector.
        :return: str
        """
        return self._meta.symbol

    @property
    def color(self) -> QColor:
        """
        Returns the color of the connector.
        :return: QColor
        """
        return QColor(self._visual.pen_foreground.color())

    @symbol.setter
    @validator
    def symbol(self, value: str):
        """
        Sets the symbol associated with the connector.
        :param value: The new symbol for the connector.
        """
        self._meta.symbol = value

    @color.setter
    @validator
    def color(self, value: QColor):
        """
        Sets the color of the connector.
        :param value: The new color for the connector.
        """
        self._visual.pen_foreground.setColor(value)
        self._visual.pen_background.setColor(value.darker(150))
        self.update()

    @property
    def origin(self) -> Optional[Handle]:
        """
        Returns the origin handle of the connector.
        :return: Handle or None
        """
        return self._meta.origin() if self._meta.origin else None

    @property
    def target(self) -> Optional[Handle]:
        """
        Returns the target handle of the connector.
        :return: Handle or None
        """
        return self._meta.target() if self._meta.target else None