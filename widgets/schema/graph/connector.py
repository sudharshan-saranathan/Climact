from widgets.schema.graph.handle import *
from widgets import schema

class Conic(Enum):
    LINE   = 1
    MANH   = 2
    BEZIER = 3

class Wisp(QGraphicsObject):

    # Constructor:
    def __init__(self, path, color, parent=None):
        super().__init__(parent)
        self._path  = path
        self._color = color
        self._width = 2.0
        self._progress = 0
        self._rect  = QRectF(-self._width * 20, -self._width * 20, self._width * 40, self._width * 40)

        self.setZValue(-1)

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):

        gradient = QLinearGradient(-self._width * 20, 0, self._width * 20, 0)
        gradient.setColorAt(0.0  , QColor(self._color))
        gradient.setColorAt(1.0  , QColor(self._color))
        gradient.setColorAt(0.5, QColor(0xffffff))

        connector = self.parentItem()
        if isinstance(connector, Connector):
            # Convert 1D path into an enclosed filled stroke region
            stroker = QPainterPathStroker()
            stroker.setWidth(self._width)                       # Make it as thick as the connector
            stroke  = stroker.createStroke(connector.path())    # Get enclosed region

            # Map to local coordinates:
            clip_path = self.mapFromScene(stroke)
            painter.setClipPath(clip_path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.boundingRect(), 1, 1)

    def get_progress(self):
        return self._progress

    def set_color(self, color):
        self._color = QColor(color)

    def set_progress(self, progress):
        self._progress = progress
        pos = self._path.pointAtPercent(progress)
        self.setPos(pos)

    @property
    def thickness(self):
        return self._width

    @thickness.setter
    def thickness(self, __value):
        self._width = __value if isinstance(__value, int) else self.thickness

    progress = pyqtProperty(float, get_progress, set_progress)

class Connector(QGraphicsObject):

    # Signals:
    sig_item_deleted = pyqtSignal()

    # Attrib:
    class Attr:
        def __init__(self):
            self.rect = QRectF(-5, -5, 10, 10)
            self.path = QPainterPath()
            self.type = QGraphicsItem.UserType + 4

    # Metadata:
    class Meta:
        reusable = list()

    # Style:
    class Style:
        def __init__(self):
            self.pen_default = QPen(Qt.GlobalColor.darkGray, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)

    # Bubble-label:
    class BubbleLabel(QGraphicsObject):

        # Constructor:
        def __init__(self, text: str, parent: QGraphicsItem = None):
            super().__init__(parent)

            # Text attributes:
            self._rect  = QRectF(-18, -10, 36, 20)
            self._label = Profile(text, False, self)
            self._label.setDefaultTextColor(QColor(0x000000))
            self._label.set_alignment(Qt.AlignmentFlag.AlignCenter)
            self._label.setTextWidth(40)
            self._label.setPos(-20, -12)

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

    # Constructor:
    def __init__(self, origin: Handle = None, target: Handle = None):
        super().__init__()

        # Attrib:
        self._attr = self.Attr()
        self._styl = self.Style()
        self._meta = self.Meta()
        self._text = None

        # Behaviour:
        self.setZValue(-1)

        # Finish if initialized without origin & target handles:
        if origin is None or target is None:
            return

        if not isinstance(origin, Handle) or not isinstance(target, Handle):
            return

        if origin.stream() == Stream.PAR or target.stream() == Stream.PAR:
            return

        # Else, continue. Store metadata:
        self._text = self.BubbleLabel(self.construct_symbol(), self)
        self._text.setPos(0, 0)

        self.origin = origin if origin.stream() == Stream.OUT else target
        self.target = target if target.stream() == Stream.INP else origin

        self.origin.connected = True
        self.target.connected = True

        self.origin.connector = self
        self.target.connector = self
        origin.conjugate = target
        target.conjugate = origin

        # Connect handles' signals to slots:
        self.origin.sig_item_shifted.connect(self.refresh)
        self.target.sig_item_shifted.connect(self.refresh)

        # Initialize animation:
        self._wisp = Wisp(self._attr.path, self.origin.color, self)
        self._anim = QPropertyAnimation(self._wisp, b"progress")

        self._anim.setDuration(1000)
        self._anim.setStartValue(0)
        self._anim.setEndValue(1)

        self._anim.finished.connect(self.time_delay)
        self._anim.start()
        self._time = QTimer(self)

        # Draw path and update:
        self.color = origin.color
        self.connect(origin.scenePos(), target.scenePos())
        self.setObjectName(QSS.random_id(length = 4, prefix = "C#"))

    # Returns the current path:
    def path(self):
        return self._attr.path

    # Returns this connector's unique identifier:
    def nuid(self):
        return self.objectName()

    # Returns user-defined type:
    def type(self):
        return self._attr.type

    @property
    def symbol(self):
        return self._text.label

    @property
    def color(self):
        return self._styl.pen_default.color()

    @color.setter
    def color(self, value: QColor):

        # Change color:
        if isinstance(value, QColor):
            self._styl.pen_default.setColor(value)
            self._wisp.set_color(value)

    @property
    def thickness(self):
        return self._styl.pen_default.width()

    @thickness.setter
    def thickness(self, __value: int):
        thick = __value if isinstance(__value, int) else self.thickness
        self._styl.pen_default.setWidth(thick)
        self._wisp.thickness = __value

    # Clear current path:
    def clear(self):
        self._attr.path.clear()
        self.update()

    # Delete item:
    def delete(self):

        # First, safe-delete the animation and the timer:
        self._anim.stop()
        self._anim.setTargetObject(None)
        self._anim.deleteLater()

        self._time.stop()
        self._time.timeout.disconnect()
        self._time.deleteLater()

        # Delete wisp:
        self._wisp.setParentItem(None)
        self._wisp.hide()
        self._wisp.deleteLater()

        # If the connector connects valid streams:
        if self._text:
            self._meta.reusable.append(int(self._text.label.split('X')[1]))

        # Reset meta-variables:
        self.origin.connected = False
        self.target.connected = False
        self.origin.connector = None
        self.target.connector = None
        self.origin.conjugate = None
        self.target.conjugate = None

        # Notify database-managers:
        self.sig_item_deleted.emit()

        # Disconnect all signals and delete:
        self.disconnect()
        self.deleteLater()

    # Event-handler for paint events:
    def paint(self, painter, option, widget = ...):
        painter.setPen(self._styl.pen_default)
        painter.drawPath(self._attr.path)

    # Returns bounding rectangle:
    def boundingRect(self):
        return self._attr.rect

    # Introduce a time delay between successive animation triggers:
    def time_delay(self):
        self._wisp.hide()
        self._time.timeout.connect(self.start_animation)
        self._time.setSingleShot(True)
        self._time.start(10000)

    # Starts the animation:
    def start_animation(self):
        self._wisp.show()
        self._anim.start()

    # Connects two coordinates with a path:
    def connect(self, opos: QPointF, tpos: QPointF):

        self.prepareGeometryChange()
        self.construct_bezier(opos, tpos)
        self._attr.rect = self._attr.path.boundingRect()

        if self._text:
            self._text.setPos(self._attr.path.boundingRect().center())

        self.update()

    # Reconstructs the path when handles have moved:
    @pyqtSlot()
    def refresh(self):
        if not self.origin or not self.target:
            return

        opos = self.origin.scenePos()
        tpos = self.target.scenePos()
        self.connect(opos, tpos)

    # Straight-line path:
    def construct_line(self, opos: QPointF, tpos: QPointF):
        self._attr.path.clear()         # Reset path
        self._attr.path.moveTo(opos)    # Go to origin
        self._attr.path.lineTo(tpos)    # Draw line to target
        return self._attr.path

    # Bezier curve:
    def construct_bezier(self, opos: QPointF, tpos: QPointF):
        self._attr.path.clear()         # Reset path

        # Initialize control-points:
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

        return self._attr.path

    # Fetch symbol:
    def construct_symbol(self):

        prefix = "X"
        if len(self._meta.reusable) and min(self._meta.reusable) <= len(schema.Canvas.edges):
            c_symbol = min(self._meta.reusable)

            self._meta.reusable.remove(c_symbol)
            return prefix + str(c_symbol)

        else:
            c_symbol = prefix + str(len(schema.Canvas.edges))
            return c_symbol