"""
terminal.py
"""
import logging
import dataclasses

from PyQt6.QtCore import (
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

from custom  import EntityRole
from util    import *
from .handle import Handle

class StreamTerminal(QGraphicsObject):
    """
    Represents an entity-terminal in the schema graph.
    """
    # Signals:
    sig_handle_clicked = pyqtSignal(Handle)     # Emitted when the terminal's handle is clicked
    sig_handle_updated = pyqtSignal(Handle)     # Emitted when the terminal is updated
    sig_item_removed   = pyqtSignal()           # Emitted when the user deletes the terminal

    # Constants:
    @dataclasses.dataclass
    class Constants:
        """
        Constants for the StreamTerminal class.
        """
        ICON_WIDTH  = 16 # Width of the icon
        ICON_OFFSET = 1  # Offset of the icon from the terminal's left/right edge

    # Visual attributes:
    @dataclasses.dataclass
    class Visual:
        """
        The terminal's visual attributes.
        """
        pen_select = QPen  (0xffa347, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        pen_border = QPen  (Qt.GlobalColor.black)
        background = QBrush(Qt.GlobalColor.lightGray)

    # Initializer:
    @validator
    def __init__(self, 
                 role: EntityRole,
                 parent : QGraphicsObject | None = None):
        """
        Initializes a new instance of the StreamTerminal class.
        :param role:
        :param parent:
        """
        # Initialize base-class:
        super().__init__(parent)

        # Initialize attribute(s):
        self._role = role
        self._tuid = random_id(prefix='T')
        self._rect = QRectF(-60, -10, 120, 20)  # Default rectangle size
        self._visual = self.Visual()

        # Load icon according to `role`:
        if  role == EntityRole.OUT:
            xpos = self._rect.left() + self.Constants.ICON_OFFSET
            icon = QGraphicsSvgItem("rss/icons/source.svg", self)

            icon.setScale(self.Constants.ICON_WIDTH / icon.boundingRect().width())
            icon.setPos(xpos, -8)

        elif role == EntityRole.INP:
            xpos = self._rect.right() - self.Constants.ICON_WIDTH - self.Constants.ICON_OFFSET
            icon = QGraphicsSvgItem("rss/icons/sink.svg", self)

            icon.setScale(self.Constants.ICON_WIDTH / icon.boundingRect().width())
            icon.setPos(xpos, -8)

        # Customize behavior:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        # Create a handle and position it:
        self.offset = QPointF(self._rect.right() - 5 if role == EntityRole.OUT else self._rect.left() + 5, 0)
        self.handle = Handle(role, "Resource", "Default", self)
        self.handle.setPos(self.offset)
        self.handle.movable  = False
        self.handle.contrast = True

        # Re-emit the handle's signal to propagate it to the Canvas:
        self.handle.sig_item_clicked.connect(lambda: self.sig_handle_clicked.emit(self.handle))
        self.handle.sig_item_updated.connect(lambda: self.on_handle_updated(self.handle))

        # Initialize context-menu:
        self._menu = QMenu()
        delete = self._menu.addAction("Delete")
        delete.triggered.connect(self.sig_item_removed.emit)

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
        return self._rect

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
        painter.setPen  (self._visual.pen_select if self.isSelected() else self._visual.pen_border)
        painter.setBrush(self._visual.background)
        painter.drawRoundedRect(self._rect, 8, 8)

    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. contextMenuEvent       Displays the _node's context menu.
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
    # 1. clone                  Duplicates the terminal.
    # ------------------------------------------------------------------------------------------------------------------

    def clone(self):
        """
        Duplicates the terminal and returns a new instance.
        :return: StreamTerminal
        """

        terminal = StreamTerminal(self._role)
        terminal.setPos(self.scenePos() + QPointF(25, 25))
        terminal.setSelected(True)

        # Map cloned handle to the original handle:
        Handle.clone_map[self.handle] = terminal.handle

        # Copy attribute(s):
        terminal.handle.import_data(self.handle)
        self.setSelected(False)

        # Return reference:
        return terminal

    @pyqtSlot(Handle)
    @validator
    def on_handle_updated(self, handle: Handle):
        """
        Event handler for when the handle is updated.
        :param: handle: The handle that was updated.
        """
        # Set the terminal's background color to the handle's color:
        strid = self.handle.strid
        color = self.scene().db.kind.get(strid, Qt.GlobalColor.lightGray)

        self._visual.background = color

    # Properties -------------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. uid                    The terminal's unique identifier.
    # 2. role                   The terminal's role (Input or Output).
    # ------------------------------------------------------------------------------------------------------------------

    @property
    def uid(self) -> str:
        """
        Returns the terminal's unique identifier (TUID).
        :return: str
        """
        return self._tuid

    @property
    def name(self) -> str:
        """
        Returns the terminal's name.
        :return: str
        """
        return self.handle.label

    @property
    def role(self):
        """
        Returns the terminal's role (input or output).
        :return: EntityRole
        """
        return self._role

    @validator
    def handle_offset(self, role: EntityRole) -> float:
        """
        Returns the offset of the node's anchor for the specified role.
        :param role: The role of the anchor (e.g., INP, OUT).
        :return: float: The x-position of the anchor in the node's coordinate system.
        """
        return -55 if role == EntityRole.INP else 55