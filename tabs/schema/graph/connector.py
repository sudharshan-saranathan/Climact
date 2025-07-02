import logging 
import weakref
import numpy as np

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsSceneMouseEvent

from custom import Label, EntityClass
from util import *
from enum import Enum

from tabs.schema.graph.handle import Handle

class PathGeometry(Enum):
    LINE = 1
    RECT = 2
    BEZIER = 3
    HEXAGON = 4

# Bubble-label:
class BubbleLabel(QGraphicsObject):

    # Constructor:
    def __init__(self, _text: str, _parent: QGraphicsItem = None):

        # Initialize super-class:
        super().__init__(_parent)

        # Text attributes:
        self._rect  = QRectF(-18, -10, 36, 20)
        self._label = Label(self, _text,
                            align=Qt.AlignmentFlag.AlignCenter,
                            width=30,
                            editable=False)

        self._label.setPos(-15, -11)

    @property
    def label(self):
        return self._label.toPlainText()

    @label.setter
    def label(self, value: str):
        self._label.setPlainText(value)

    def paint(self, painter, option, widget = ...):
        painter.setPen(QColor(0x000000))
        painter.setBrush(QColor(0xffffff))
        painter.drawRoundedRect(self._rect, 8, 8)

    def boundingRect(self):
        return self._rect

class Connector(QGraphicsObject):

    # Signals:
    sig_item_removed = pyqtSignal()

    # Attrib:
    class Attr:
        def __init__(self):
            self.rect = QRectF(-10, -10, 20, 20)
            self.path = QPainterPath()
            self.geom = PathGeometry.HEXAGON

    # Style:
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.darkGray, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            self.pen_select = QPen(Qt.GlobalColor.darkGray, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

    # Initializer:
    def __init__(self,
                 symbol: str,
                 origin: Handle | None = None,
                 target: Handle | None = None,
                 overwrite: bool = True,
                 parent: QGraphicsObject | None = None):

        # Initialize base-class:
        super().__init__(parent)

        # Attrib:
        self._cuid = random_id(length=4, prefix='C')
        self._attr = self.Attr()
        self._styl = self.Style()
        self._text = None
        self._is_obsolete = False

        # Direction arrows:
        self._dir_w = load_svg("rss/icons/direction.svg", 14)
        self._dir_e = load_svg("rss/icons/direction.svg", 14)

        self._dir_w.setParentItem(self)
        self._dir_e.setParentItem(self)

        # Customize behavior:   
        self.setZValue(-1)

        # Return if `origin` or `target` is None:
        if (
            origin is None or
            target is None
        ):  
            return

        # Abort-conditions:
        if origin == target:                           raise ValueError("Origin and target handles must be different")
        if origin.eclass == EntityClass.PAR:            raise ValueError("Origin handle must be of INP/OUT stream")
        if target.eclass == EntityClass.PAR:            raise ValueError("Target handle must be of INP/OUT stream")
        if origin.eclass == target.eclass:             raise ValueError("Origin and target handles must be of different streams")
        if origin.parentItem() == target.parentItem(): raise ValueError("Origin and target handles belong to different nodes or terminals")

        # Initialize bubble-label and direction-arrows:
        self._text  = BubbleLabel(symbol, self)

        # Store references:
        self.origin = origin if origin.eclass == EntityClass.OUT else target
        self.target = target if target.eclass == EntityClass.INP else origin

        # Setup references in handles:
        self.origin.lock(self.target, self)
        self.target.lock(self.origin, self)

        # Connect handles' signals to slots:
        self.origin.sig_item_updated.connect(self.on_origin_updated)    # Emit signal to notify the application that origin is now connected
        self.origin.sig_item_shifted.connect(self.redraw)               # Connect origin's `sig_item_shifted` signal to `redraw`
        self.target.sig_item_shifted.connect(self.redraw)               # Connect target's `sig_item_shifted` signal to `redraw`

        # If either of the handles is destroyed, set obsolete:
        self.origin.destroyed.connect(self.set_obsolete)                # If the origin handle is destroyed, make the connector obsolete
        self.target.destroyed.connect(self.set_obsolete)                # If the target handle is destroyed, make the connector obsolete

        # Assign origin's data to target:
        if overwrite:
            
            self.target.strid   = self.origin.strid     # Copy stream ID
            self.target.color   = self.origin.color     # Copy color
            self.target.units   = self.origin.units     # Copy units
            self.target.value   = self.origin.value     # Copy value
            self.target.sigma   = self.origin.sigma     # Copy sigma
            self.target.minimum = self.origin.minimum   # Copy minimum
            self.target.maximum = self.origin.maximum   # Copy maximum

        # Notify the application that the target handle has been updated:
        self.target.rename(self.origin.label)
        self.target.sig_item_updated.emit(self.target)                  # Emit signal to notify application that `target` has been updated

        # Update color, and redraw path:
        self.set_color(self.origin.color)
        self.draw(self.origin.scenePos(), self.target.scenePos(), self.geometry)

    @property
    def path(self): return self._attr.path

    @property
    def uid(self):  return self._cuid

    @property
    def symbol(self):   return self._text.label

    @property
    def geometry(self): return self._attr.geom

    def boundingRect(self): return self._attr.path.boundingRect().adjusted(-10, -10, 10, 10)

    def paint(self, painter, option, widget=None):
        painter.setPen(self._styl.pen_border)
        painter.drawPath(self._attr.path)
    
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        
        # Debugging:
        print(f"Connector.mouseDoubleClickEvent(): {self.symbol} {self.origin.connected} {self.target.connected}")

        return super().mouseDoubleClickEvent(event)

    def clear(self):
        self._dir_w.hide()
        self._dir_e.hide()
        self._attr.path.clear()

    def on_origin_updated(self):
        if self._is_obsolete:
            return

        self._styl.pen_border = QPen(self.origin.color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        if  self.origin.connected:
            self.target.strid = self.origin.strid
            self.target.color = self.origin.color
            self.target.sig_item_updated.emit(self.target)

    def draw(self, opos: QPointF, tpos: QPointF, geometry: PathGeometry):

        # Reset path:
        self.prepareGeometryChange()        # Required to trigger repainting when the path changes
        self._attr.path.clear()             # Clear the path

        # Construct curve:
        if  geometry == PathGeometry.LINE:
            self.construct_segment(opos, tpos)

        elif geometry == PathGeometry.BEZIER:
            self.construct_bezier(opos, tpos)

        elif geometry == PathGeometry.HEXAGON:
            self.construct_hexagonal(opos, tpos)

        elif geometry == PathGeometry.RECT:
            self.construct_manhattan(opos, tpos)

        if self._text:
            self._text.setPos(self._attr.path.boundingRect().center())

    @pyqtSlot()
    @pyqtSlot(Handle)
    def redraw(self, handle: Handle | None = None):

        # Null-check:
        if  self._is_obsolete:
            print("Connector.redraw(): Reference(s) obsolete. Aborting!")
            return

        opos = self.origin.scenePos()
        tpos = self.target.scenePos()

        self.draw(opos, tpos, self._attr.geom)
        self.update()

    def set_obsolete(self)  -> None:    self._is_obsolete = True

    def set_relevant(self)  -> None:    self._is_obsolete = False

    def set_color(self, _color: QColor):

        # Change pen-color:
        self._styl.pen_border.setColor(_color)

    # Line-segment:
    def construct_segment(self, opos: QPointF, tpos: QPointF):
        self._attr.path.moveTo(opos)
        self._attr.path.lineTo(tpos)

    # Rectilinear:
    def construct_manhattan(self, opos: QPointF, tpos: QPointF):

        # Define mid points:
        xm = (opos.x() + tpos.x()) /  2.0   # Midpoint x-coordinate
        r1 = (tpos.y() - opos.y()) / 25.0   # Arc-radius in the y-direction
        r2 = (tpos.x() - opos.x()) / 25.0   # Arc-radius in the x-direction
        r  = min([abs(r1), abs(r2)])        # Min arc-radius

        if opos.x() < tpos.x() and opos.y() < tpos.y():
            self._attr.path.moveTo(opos)
            self._attr.path.lineTo(xm - r, opos.y())
            self._attr.path.arcTo (xm - r, opos.y(), 2*r, 2*r, 90, -90)
            self._attr.path.lineTo(xm + r, tpos.y() - 2*r)
            self._attr.path.arcTo (xm + r, tpos.y() - 2*r, 2*r, 2*r, 180, 90)
            self._attr.path.lineTo(tpos)

        elif opos.x() < tpos.x() and opos.y() >= tpos.y():
            self._attr.path.moveTo(opos)
            self._attr.path.lineTo(xm - r, opos.y())
            self._attr.path.arcTo (xm - 2*r, opos.y() - 2*r, 2*r, 2*r, 270, 90)
            self._attr.path.lineTo(xm, tpos.y() + r)
            self._attr.path.arcTo (xm, tpos.y(), 2*r, 2*r, 180, -90)
            self._attr.path.lineTo(tpos)

        elif opos.x() >= tpos.x() and opos.y() < tpos.y():
            self._attr.path.moveTo(opos)
            self._attr.path.lineTo(xm + r, opos.y())
            self._attr.path.arcTo (xm, opos.y(), 2*r, 2*r, 90, 90)
            self._attr.path.lineTo(xm, tpos.y() - r)
            self._attr.path.arcTo (xm - 2*r, tpos.y() - 2*r, 2*r, 2*r, 0, -90)
            self._attr.path.lineTo(tpos)

        elif opos.x() >= tpos.x() and opos.y() >= tpos.y():
            self._attr.path.moveTo(opos)
            self._attr.path.lineTo(xm + r, opos.y())
            self._attr.path.arcTo (xm, opos.y()-2*r, 2*r, 2*r, 270, -90)
            self._attr.path.lineTo(xm, tpos.y() +r)
            self._attr.path.arcTo (xm - 2*r, tpos.y(), 2*r, 2*r, 0, 90)
            self._attr.path.lineTo(tpos)

    # Hexagonal:
    def construct_hexagonal(self, opos: QPointF, tpos: QPointF):
        """
        Draws a hexagonal path between the origin and target handles.
        """

        t = np.pi / 6.0 if tpos.y() > opos.y() else 5 * np.pi / 6.0
        xm = 0.50 * (opos.x() + tpos.x())
        xd = np.tan(t) * (tpos.y() - opos.y()) / 2.0
        r = min(0.50 * xd, 5)

        self._attr.path.clear()
        self._attr.path.moveTo(opos)

        self._dir_w.setPos((opos.x() + xm - xd) / 2.0 - 7, opos.y() - 7)
        self._dir_e.setPos((tpos.x() + xm + xd) / 2.0 - 7, tpos.y() - 7)

        # If the origin is to the left of the target, draw the path accordingly:
        if opos.x() < tpos.x():
            self._attr.path.lineTo(xm - xd - r, opos.y())
            self._attr.path.quadTo(xm - xd, opos.y(), xm - xd + r * np.sin(t), opos.y() + r * np.cos(t))
            self._attr.path.lineTo(xm + xd - r * np.sin(t), tpos.y() - r * np.cos(t))
            self._attr.path.quadTo(xm + xd, tpos.y(), xm + xd + r, tpos.y())

        else:
            self._attr.path.lineTo(xm + xd + r, opos.y())
            self._attr.path.quadTo(xm + xd, opos.y(), xm + xd - r * np.sin(t), opos.y() + r * np.cos(t))
            self._attr.path.lineTo(xm - xd + r * np.sin(t), tpos.y() - r * np.cos(t))
            self._attr.path.quadTo(xm - xd, tpos.y(), xm - xd - r, tpos.y())

        self._attr.path.lineTo(tpos)

    # Bezier curve:
    def construct_bezier(self, opos: QPointF, tpos: QPointF):

        # Define control-points for the spline curve:
        xi = opos.x()
        yi = opos.y()
        xf = tpos.x()
        yf = tpos.y()
        xm = (xi + xf) / 2.0
        dx = 0.25 * (xf - xi)
        ep = 0.45 * dx

        # Draw path:
        self._attr.path.moveTo(opos)
        self._attr.path.lineTo(xm - dx - ep, yi)
        self._attr.path.cubicTo(xm, yi, xm, yf, xm + dx + ep, yf)
        self._attr.path.lineTo(xf, yf)