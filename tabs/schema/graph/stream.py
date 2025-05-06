from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal, QPoint
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QIcon, QTextCursor
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsItem, QMenu

from core.label import Label
from core.util import anti_color, random_id
from tabs.schema.action import CreateStreamAction
from tabs.schema.graph.handle import Handle
from tabs.schema.graph.anchor import StreamType

class Stream(QGraphicsObject):

    # Signals:
    sig_socket_clicked = pyqtSignal(Handle)
    sig_stream_deleted = pyqtSignal()

    # Default style:
    class Style:
        def __init__(self):
            self.pen_select = QPen(Qt.GlobalColor.black)
            self.pen_border = QPen(Qt.GlobalColor.darkGray)
            self.background = QBrush(Qt.GlobalColor.darkGray)

    # Default Attrib:
    class Attr:
        def __init__(self):
            self.rect  = QRectF(-50, -10, 100, 20)

    # Initializer:
    def __init__(self, parent: QGraphicsObject | None, label: str, stream: StreamType):

        # Initialize base-class:
        super().__init__(parent)

        # Initialize attribute(s):
        self._attr  = self.Attr()
        self._suid  = random_id(length=4, prefix='S')
        self._style = self.Style()

        # Add icon:
        file = "rss/icons/source.svg" if stream == StreamType.OUT else "rss/icons/sink.svg"
        ipos = -33 if stream == StreamType.INP else 48
        self._icon = QGraphicsSvgItem(file, self)
        self._icon.setScale(0.06)
        self._icon.setPos(-ipos, -7.5)

        # Add text-description:
        self._label = Label(self,
                            align=Qt.AlignmentFlag.AlignCenter,
                            font=QFont("Fira Sans", 12),
                            edit=False,
                            label=label,
                            width=60)
        self._label.setDefaultTextColor(anti_color(QColor(Qt.GlobalColor.darkGray)))
        self._label.setPos(-30, -11)
        self._stream = stream

        # Customize behavior:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        # Create handle and position it:
        offset = -44 if stream == StreamType.INP else 44
        self.socket = Handle(QPointF(offset, 0), str(), self._stream, self)
        self.socket.isLabeled = False
        self.socket.sig_item_clicked.connect(lambda: self.sig_socket_clicked.emit(self.socket))
        self.socket.sig_item_updated.connect(self.update_background)

        # Initialize context-menu:
        self._init_menu()

    # Initialize menu:
    def _init_menu(self):

        # Setup menu:
        self._menu = QMenu()
        _edit = self._menu.addAction("Edit Label")
        _edit.triggered.connect(self.edit_label)

        _delete = self._menu.addAction("Delete")
        _delete.triggered.connect(self.sig_stream_deleted.emit)

    @property
    def uid(self)   -> str: return self._suid

    @property
    def label(self) -> str: return self._label.toPlainText()

    @label.setter
    def label(self, value): self._label.setPlainText(str(value))

    @property
    def stream(self): return self._stream

    # Return bounding-rectangle:
    def boundingRect(self):
        return self._attr.rect

    # Paint:
    def paint(self, painter, option, widget = ...):
        painter.setPen  (self._style.pen_select if self.isSelected() else self._style.pen_border)
        painter.setBrush(self._style.background)
        painter.drawRoundedRect(self._attr.rect, 12, 10)

    # Duplicate:
    def duplicate(self, canvas):

        stream = Stream(None, self._label.toPlainText(), self._stream)
        stream.setPos(self.scenePos() + QPointF(25, 25))
        stream._style.background = self._style.background

        # Create hash-map entry:
        Handle.cmap[self.socket] = stream.socket

        # Copy properties:
        stream.socket.label   = self.socket.label
        stream.socket.units   = self.socket.units
        stream.socket.value   = self.socket.value
        stream.socket.sigma   = self.socket.sigma
        stream.socket.cname   = self.socket.cname
        stream.socket.color   = self.socket.color
        stream.socket.minimum = self.socket.minimum
        stream.socket.maximum = self.socket.maximum

        # Return reference:
        return stream, CreateStreamAction(canvas, stream)

    # Context-menu event handler:
    def contextMenuEvent(self, event):
        self._menu.exec(event.screenPos())

    # Hover-enter:
    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverEnterEvent(event)

    # Hover-leave:
    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverLeaveEvent(event)

    # Change background-color when the handle's category is changed:
    def update_background(self, handle: Handle):

        # Type-check:
        if not isinstance(handle, Handle):
            print(f"Error: Expected argument of type <Handle>")
            return

        # Change background-color:
        self._style.pen_border = handle.color
        self._style.background = handle.color
        self._label.setDefaultTextColor(anti_color(handle.color))
        self.update()

    # Make the handle's label temporarily editable:
    def edit_label(self):

        # Make the label temporarily editable:
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._label.setFocus(Qt.FocusReason.OtherFocusReason)

        # Highlight the entire word:
        cursor = self._label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        self._label.setTextCursor(cursor)

    def free(self):
        # Disconnect stream and delete connector:
        if  self.socket.connected:
            self.socket.conjugate().free()
            self.socket.connector().deleteLater()