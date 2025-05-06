from PyQt6.QtCore import pyqtSignal, QRect, Qt, QPointF, QRectF, pyqtSlot
from PyQt6.QtGui import QPainterPath, QPainter, QPen, QBrush, QPainterPathStroker, QColor, QFont
from PyQt6.QtWidgets    import QGraphicsObject, QGraphicsItem

from core.category import Category
from core.label import Label
from core.util import random_id
from tabs import schema
from enum import Enum

from tabs.schema.graph.anchor import StreamType
from tabs.schema.graph.handle import Handle

class PathGeometry(Enum):
    LINE = 1
    RECT = 2
    BEZIER = 3

# Bubble-label:
class BubbleLabel(QGraphicsObject):

    # Constructor:
    def __init__(self, text: str, parent: QGraphicsItem = None):

        # Initialize super-class:
        super().__init__(parent)

        # Text attributes:
        self._rect  = QRectF(-18, -10, 36, 20)
        self._label = Label(self,
                            edit=False,
                            font=QFont("Fira Sans", 12),
                            width=30,
                            label=text,
                            color=QColor(0x0),
                            align=Qt.AlignmentFlag.AlignCenter)

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
            self.geom = PathGeometry.BEZIER

    # Style:
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.darkGray, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            self.pen_select = QPen(Qt.GlobalColor.darkGray, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

    # Initializer:
    def __init__(self, parent: QGraphicsObject | None, overwrite=True, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # Attrib:
        self._cuid = random_id(length=4, prefix='C')
        self._attr = self.Attr()
        self._styl = self.Style()
        self._text = None
        self._is_obsolete = False

        # Customize behavior:
        self.setZValue(-1)

        # Check if valid origin and target handles were provided:
        if (
            not bool(kwargs.get("origin"))              or  # If no origin handle was provided
            not bool(kwargs.get("target"))              or  # If no target handle was provided
            not isinstance(kwargs["origin"], Handle)    or  # If the origin object is not a handle
            not isinstance(kwargs["target"], Handle)    or  # If the target object is not a handle
            kwargs["origin"].stream == StreamType.PAR   or  # If the origin handle is not of INP/OUT StreamType
            kwargs["target"].stream == StreamType.PAR       # If the target handle is not of INP/OUT StreamType
        ):
            return

        # Store weak-references to the handles:
        self.origin = kwargs["origin"]
        self.target = kwargs["target"]

        # Setup references:
        self.origin.lock(self.target, self)
        self.target.lock(self.origin, self)

        # Connect handles' signals to slots:
        self.origin.sig_item_updated.connect(self.on_origin_updated)
        self.origin.sig_item_shifted.connect(self.redraw)
        self.target.sig_item_shifted.connect(self.redraw)

        # If either of the handles are destroyed, set obsolete:
        self.origin.destroyed.connect(self.set_obsolete)
        self.target.destroyed.connect(self.set_obsolete)

        # Assign origin's data to target:
        if overwrite:
            self.target.cname   = self.origin.cname
            self.target.color   = self.origin.color
            self.target.units   = self.origin.units
            self.target.value   = self.origin.value
            self.target.sigma   = self.origin.sigma
            self.target.minimum = self.origin.minimum
            self.target.maximum = self.origin.maximum

        self.target.sig_item_updated.emit(self.target)

        # Setup label:
        self._text = BubbleLabel(kwargs["symbol"], self)
        self._styl.pen_border = QPen(self.origin.color, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

        # Redraw the path:
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
        pen_active = self._styl.pen_select if self.isSelected() else self._styl.pen_border
        painter.setPen(pen_active)
        painter.drawPath(self._attr.path)

    def clear(self):    self._attr.path.clear()

    def delete(self):

        if self._is_obsolete:           return
        if self.origin == self.target:  return

        self.origin.free()
        self.target.free()

        # Schedule for deletion:
        self.deleteLater()

    def on_origin_updated(self):

        if self._is_obsolete:           return
        if self.origin == self.target:  return

        self._styl.pen_border = QPen(self.origin.color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        if  self.origin.connected:
            self.target.cname = self.origin.cname
            self.target.color = self.origin.color
            self.target.sig_item_updated.emit(self.target)

    def draw(self, opos: QPointF, tpos: QPointF, geometry: PathGeometry):

        if (
            not isinstance(opos, QPointF) or
            not isinstance(tpos, QPointF)
        ):
            print(f"Connector.draw(): [ERROR] Expected arguments of type QPointF")
            return

        # Reset path:
        self.prepareGeometryChange()        # Required to trigger repainting when the path changes
        self._attr.path.clear()             # Clear the path

        # Construct curve:
        if  geometry == PathGeometry.LINE:
            self.construct_segment(opos, tpos)

        elif geometry == PathGeometry.BEZIER:
            self.construct_bezier(opos, tpos)

        elif geometry == PathGeometry.RECT:
            self.construct_manhattan(opos, tpos)

        if self._text:
            self._text.setPos(self._attr.path.boundingRect().center())

    @pyqtSlot()
    @pyqtSlot(Handle)
    def redraw(self, handle: Handle | None = None):

        # Null-check:
        if self._is_obsolete:
            print("Connector.redraw(): Reference(s) obsolete. Aborting!")
            return

        opos = self.origin.scenePos()
        tpos = self.target.scenePos()

        self.draw(opos, tpos, self._attr.geom)
        self.update()

    def set_obsolete(self)  -> None:    self._is_obsolete = True

    def set_relevant(self)  -> None:    self._is_obsolete = False

    # Line-segment:
    def construct_segment(self, opos: QPointF, tpos: QPointF):
        self._attr.path.moveTo(opos)
        self._attr.path.lineTo(tpos)

    # Rectilinear:
    def construct_manhattan(self, opos: QPointF, tpos: QPointF):

        # Define mid points:
        xm = (opos.x() + tpos.x()) /  2.0   # Midpoint x-coordinate
        r1 = (tpos.y() - opos.y()) / 20.0   # Arc-radius in the y-direction
        r2 = (tpos.x() - opos.x()) / 20.0   # Arc-radius in the x-direction
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