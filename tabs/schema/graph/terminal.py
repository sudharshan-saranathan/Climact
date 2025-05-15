import logging

from PyQt6.QtCore import (
    Qt, 
    QRectF, 
    QPointF, 
    pyqtSlot,
    pyqtSignal
)

from PyQt6.QtGui import (
    QPen, 
    QBrush
)

from PyQt6.QtWidgets import (
    QGraphicsObject, 
    QGraphicsItem, 
    QMenu
)

from custom  import EntityClass
from util    import *
from .handle import Handle

class StreamTerminal(QGraphicsObject):

    # Signals:
    sig_terminal_clicked = pyqtSignal() # Emitted when the terminal's handle is clicked
    sig_terminal_deleted = pyqtSignal() # Emitted when the terminal is deleted
    sig_terminal_updated = pyqtSignal() # Emitted when the terminal is updated

    # Constants:
    class Constants:
        ICON_WIDTH  = 16 # Width of the icon
        ICON_OFFSET = 1  # Offset of the icon from the terminal's left/right edge

    # Default style:
    class Style:
        def __init__(self):
            self.pen_select = QPen(Qt.GlobalColor.black)
            self.pen_border = QPen(Qt.GlobalColor.darkGray)
            self.background = QBrush(Qt.GlobalColor.darkGray)

    # Default Attrib:
    class Attr:
        def __init__(self):
            self.rect = QRectF(-60, -10, 120, 20)

    # Initializer:
    def __init__(self, 
                _eclass : EntityClass, 
                _parent : QGraphicsObject | None
                ):
        """
        Initialize a new stream terminal.

        Parameters:
            _eclass (EntityClass): EntityClass (INP or OUT), see custom/entity.py.
            _parent (QGraphicsObject): Parent QGraphicsObject.

        Returns: None
        """

        # Validate arguments:
        if _eclass not in [EntityClass.INP, EntityClass.OUT]:
            raise ValueError("Expected `EntityClass.INP` or `EntityClass.OUT` for argument `_eclass`")
        
        # Initialize base-class:
        super().__init__(_parent)

        # Initialize attribute(s):
        self._tuid  = random_id(length=4, prefix='T')
        self._attr  = self.Attr()
        self._style = self.Style()

        # Load icon according to `_eclass`:
        if  _eclass == EntityClass.OUT:
            _xpos = self._attr.rect.left() + self.Constants.ICON_OFFSET
            _ypos = -8

            _icon = load_svg("rss/icons/source.svg", self.Constants.ICON_WIDTH)
            _icon.setPos(_xpos, _ypos)
            _icon.setParentItem(self)

        elif _eclass == EntityClass.INP:
            _xpos = self._attr.rect.right() - self.Constants.ICON_WIDTH - self.Constants.ICON_OFFSET
            _ypos = -8

            _icon = load_svg("rss/icons/sink.svg", self.Constants.ICON_WIDTH)
            _icon.setPos(_xpos, _ypos)
            _icon.setParentItem(self)

        # Initialize entity-class:
        self._eclass = _eclass

        # Customize behavior:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        # Create handle and position it:
        self.offset = QPointF(self._attr.rect.right() - 5 if _eclass == EntityClass.OUT else self._attr.rect.left() + 5, 0)
        self.socket = Handle("Resource", self.offset, _eclass, self)
        self.socket.sig_item_updated.connect(self.on_socket_updated)

        # Initialize context-menu:
        self._menu = QMenu()
        _delete = self._menu.addAction("Delete")
        _delete.triggered.connect(self.sig_terminal_deleted.emit)


    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Returns the bounding rectangle of the terminal.
    # 2. paint                  Paints the terminal.
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self) -> QRectF:
        """
        Re-implementation of the `QGraphicsObject.boundingRect()` method.

        Returns:
            QRectF: The bounding rectangle of the terminal.
        """
        return self._attr.rect

    # Paint:
    def paint(self, painter, option, widget = ...):
        """
        Re-implementation of the `QGraphicsObject.paint()` method.

        Parameters:
            painter (QPainter) : The painter to use.
            option (QStyleOptionGraphicsItem) : The style option to use.
            widget (QWidget) : The widget to use.

        Returns: None
        """
        painter.setPen  (self._style.pen_select if self.isSelected() else self._style.pen_border)
        painter.setBrush(self._style.background)
        painter.drawRoundedRect(self._attr.rect, 12, 10)

    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. contextMenuEvent       Displays the node's context menu.
    # 2. hoverEnterEvent        Sets the cursor to an arrow when hovering over the terminal.
    # 3. hoverLeaveEvent        Unsets the cursor when leaving the terminal.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Re-implementation of the `QGraphicsObject.contextMenuEvent()` method.

        Parameters:
            event (QContextMenuEvent) : Context-menu event, triggered and managed by Qt.

        Returns: None
        """
        self._menu.exec(event.screenPos())

    def hoverEnterEvent(self, event):
        """
        Re-implementation of the `QGraphicsObject.hoverEnterEvent()` method.

        Parameters:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.

        Returns: None
        """
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Re-implementation of the `QGraphicsObject.hoverLeaveEvent()` method.

        Parameters:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.

        Returns: None
        """
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverLeaveEvent(event)

    # Custom methods ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. duplicate                Duplicates the terminal.
    # ------------------------------------------------------------------------------------------------------------------

    def duplicate(self, _canvas):
        """
        Duplicates the terminal.

        Parameters:
            _canvas (QGraphicsScene): The canvas to duplicate the terminal onto.

        Returns: 
            StreamTerminal: A new terminal with the same properties as the original terminal.
        """

        _stream = StreamTerminal(self.socket.stream, None)
        _stream.setPos(self.scenePos() + QPointF(25, 25))

        # Create hash-map entry:
        Handle.cmap[self.socket] = _stream.socket

        # Copy properties:
        _stream.socket.label   = self.socket.label
        _stream.socket.units   = self.socket.units
        _stream.socket.value   = self.socket.value
        _stream.socket.sigma   = self.socket.sigma
        _stream.socket.strid   = self.socket.strid
        _stream.socket.color   = self.socket.color
        _stream.socket.minimum = self.socket.minimum
        _stream.socket.maximum = self.socket.maximum

        # Import Canvas:
        from tabs.schema.canvas import Canvas
        if isinstance(_canvas, Canvas):
            _canvas.paste_item(_stream)

        # Return reference:
        return _stream

    @pyqtSlot(Handle)
    def on_socket_updated(self, _socket):
        """
        Event handler for when the socket is updated.
        """

        self._style.background = self.socket.color

    # Properties -------------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. uid                    The terminal's unique identifier.
    # 2. eclass                 The terminal's entity class.
    # ------------------------------------------------------------------------------------------------------------------

    @property
    def uid(self) -> str: return self._tuid

    @property
    def eclass(self): return self._eclass