"""
node.py
"""

# Standard library imports:
import qtawesome as qta
import logging
import dataclasses

# PyQt6 library:
from PyQt6.QtGui import (
    QPen,
    QBrush
)
from PyQt6.QtCore import (
    QRectF,
    QLineF,
    QPointF,
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsItem, 
    QGraphicsObject, 
)

# GraphicsObjects:
from .anchor import Anchor
from .handle import Handle

from actions import *
from custom  import *
from util    import *

# Class `Node`: A custom QGraphicsObject representing a node in a graphical schema.
class Node(QGraphicsObject):
    """
    An interactive `QGraphicsObject` subclass that represents a node in a graphical schema. The node includes buttons,
    labels, and other child items.
    """
    # Signals:
    sig_exec_actions   = pyqtSignal(AbstractAction)     # Signal emitted when an action is executed.
    sig_item_removed   = pyqtSignal()                   # Signal emitted when the user deletes the node.
    sig_item_updated   = pyqtSignal()                   # Signal emitted when the node has changed (e.g., position, size, label).
    sig_item_clicked   = pyqtSignal()                   # Signal emitted when the node is double-clicked.
    sig_handle_clicked = pyqtSignal(Handle)             # Signal emitted when a handle is clicked.
    sig_handle_removed = pyqtSignal(Handle)             # Signal emitted when a handle is removed.

    # Node attributes:
    @dataclasses.dataclass
    class Database:
        """
        A dataclass to hold database attributes for the node.
        """
        inp: ValidatorDict[Handle] = dataclasses.field(default_factory = lambda: ValidatorDict(Handle)) # Dictionary of input handles.
        out: ValidatorDict[Handle] = dataclasses.field(default_factory = lambda: ValidatorDict(Handle)) # Dictionary of output handles.
        par: list[Entity]          = dataclasses.field(default_factory = lambda: [])                    # Dictionary of parameters.
        eqn: list[str]             = dataclasses.field(default_factory = lambda: [])                    # List of equations.

        @validator
        def __getitem__(self, kind: EntityRole | EntityClass):
            """
            Returns the database corresponding to the specified kind (Input/Output/Variable/Parameter/Equation).
            :param kind: The role or class of the entity.
            :return:
            """
            if  kind == EntityRole.INP:
                return self.inp

            if  kind == EntityRole.OUT:
                return self.out

            if  kind == EntityClass.VAR:
                return self.inp | self.out

            if  kind == EntityClass.PAR:
                return self.par

            if  kind == EntityClass.EQN:
                return self.eqn

            return None

    # Visual attributes:
    @dataclasses.dataclass(frozen=True)
    class Visual:
        """
        A dataclass to hold visual attributes for the node.
        """
        pen_normal: QPen   = dataclasses.field(default_factory = lambda: QPen(0x000000, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        pen_select: QPen   = dataclasses.field(default_factory = lambda: QPen(0xffa347, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        background: QBrush = dataclasses.field(default_factory = lambda: QBrush(0xffffff))
        highlight : QBrush = dataclasses.field(default_factory = lambda: QBrush(QColor(0x00ff00)))

    # Instantiate dataclass `Visual`
    visual = Visual()

    # Class constructor:
    def __init__(self,
                 nuid: str,
                 name: str,
                 cpos: QPointF,
                 parent: QGraphicsItem | None = None):

        super().__init__(parent)                    # Initialize super class
        super().setAcceptHoverEvents(True)          # Accept hover events (needed to change the cursor's shape)
        super().setObjectName(f"{nuid}: {name}")    # This will allow the node to be identified using its UID and name.

        super().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        super().setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        super().setPos(cpos)

        # Custom attributes:
        self._rect = QRectF(-100, -75, 200, 150)    # The node's bounding rectangle.
        self._open = False                          # This flag is set to true when the node is double-clicked.

        # Database:
        self._db = self.Database()

        # Set up text items in the header:
        self._nuid = String(self, nuid, width=50, editable=False, align=Qt.AlignmentFlag.AlignLeft, color=QColor(0xbdbdbd))
        self._name = String(self, name, width=90)
        self._nuid.setPos(-98, -72.5)
        self._name.setPos(-45, -72.5)

        # Set up buttons in the header:
        self._expand = Button("rss/icons/expand.svg", self, lambda: self.resize( 50))
        self._shrink = Button("rss/icons/shrink.svg", self, lambda: self.resize(-50))
        self._remove = Button("rss/icons/delete.svg", self, self.sig_item_removed.emit)
        self._expand.moveBy(70, -59)
        self._shrink.moveBy(70, -65)
        self._remove.moveBy(86, -62)

        # Set up anchors:
        self._anchor_inp = Anchor(EntityRole.INP, self)
        self._anchor_out = Anchor(EntityRole.OUT, self)
        self._anchor_inp.sig_item_clicked.connect(self.on_anchor_clicked)
        self._anchor_out.sig_item_clicked.connect(self.on_anchor_clicked)

        # Display a warning or checkmark icon in the node:
        self._status = load_svg("rss/icons/warning.svg", 24)
        self._status.setParentItem(self)
        self._status.moveBy(-12, -12)
        self._status.acceptHoverEvents()
        self._status.setToolTip("This node has unused variables or parameters.")

    # Method required to be implemented by a `QGraphicsObject` subclass:
    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the node.
        """
        return self._rect

    # Method required to be implemented by a `QGraphicsObject` subclass:
    def paint(self, painter, option, widget=None):
        """
        Paints the node on the canvas using the provided painter.
        :param painter: QPainter instance used for drawing.
        :param option: QStyleOptionGraphicsItem instance containing style options.
        :param widget: Optional QWidget instance for additional context.
        """

        pen_current = Node.visual.pen_select if self.isSelected() else Node.visual.pen_normal
        painter.setPen(pen_current)
        painter.setBrush(Node.visual.background)
        painter.drawRoundedRect(self._rect, 8, 8)     # The node's border

        pen_separator = QPen(0xcfcfcf, 1.0)
        painter.setPen(pen_separator)
        painter.drawLine(QLineF(-96, -48, 96, -48))
        painter.drawLine(QLineF(  0, -42,  0, self._rect.bottom() - 6))

    #
    #
    #

    @validator
    def __getitem__(self, kind: EntityRole | EntityClass):
        """
        Returns
        :param kind:
        :return: list
        """
        return self._db[kind]

    # ------------------------------------------------------------------------------------------------------------------
    # Event handler(s)
    # Name                              Description
    # ------------------------------------------------------------------------------------------------------------------
    # hoverEnterEvent(QHoverEvent)      Adds effects (highlighting) when the cursor enters the node's bounding box.
    # hoverLeaveEvent                   Undoes hoverEnterEvent effects when the cursor exits the node's bounding box.

    def mouseDoubleClickEvent(self, event):
        """
        Event-handler for double-click events, emits the sig_item_clicked signal.
        :param event:
        """
        self._open = True
        self.sig_item_clicked.emit()

    def hoverEnterEvent(self, event):
        """
        Handles the hover enter event for the node.
        :param: event: QHoverEvent instantiated and managed by Qt.
        """
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Handles the hover leave event for the node.
        :param event: QHoverEvent instantiated and managed by Qt.
        """
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    #
    # Custom methods
    #
    #

    @validator
    def create_huid(self, role: EntityRole) -> str:
        """
        Creates a unique symbol for each handle for each role (INP, OUT).
        :param role: The role of the handle (e.g., INP, OUT).
        :return:
        """
        # Get the set of active handle IDs for the specified role:
        active_ids = set(
            int(handle.symbol[1:])
            for handle, state in self[role].items()
            if  state == EntityState.ACTIVE
        )

        # Find the lowest unused ID:
        index = 0
        while index in active_ids:
            index += 1

        # Return symbol:
        return f"R{index:02d}" if role == EntityRole.INP else f"P{index:02d}"

    @validator
    def create_handle(self, role: EntityRole, npos: QPointF) -> Handle | None:
        """
        Creates a new handle at the specified position with the given role.
        :param role: The role of the handle (e.g., INP, OUT).
        :param npos: The position where the handle should be created, in the node's coordinate system.
        :return: Handle: Handle instance.
        """
        # Abort conditions:
        if (
            not isinstance(role, EntityRole) or
            not isinstance(npos, QPointF)
        ):
            logging.error("Invalid parameters: Expected EntityRole and QPointF instances.")
            return None

        symbol = self.create_huid(role)
        handle = Handle(role, symbol, "Default", self)
        handle.setPos(npos)

        # Connect the handle's signals to event handlers:
        handle.sig_item_clicked.connect(lambda: self.sig_handle_clicked.emit(handle))
        handle.sig_item_removed.connect(self.on_handle_removed)

        # Add the handle to the node's database:
        self._db[role][handle] = EntityState.ACTIVE

        # Return a reference:
        return handle

    def clone(self) -> 'Node':
        """
        Returns a cloned instance of this node.
        :return: Node: A new instance of Node.
        """
        # Create a new node with the same UID and name:
        cloned_node = Node(
            nuid = self._nuid.toPlainText(),
            name = self._name.toPlainText(),
            cpos = self.scenePos()
        )

        # Resize the cloned node to match the original:
        cloned_node.resize(self._rect.height() - cloned_node._rect.height())

        # Clone the handles:
        for handle, state in self[EntityClass.VAR].items():
            if state == EntityState.ACTIVE:
                cloned_handle = cloned_node.create_handle(handle.role, handle.pos())
                cloned_handle.import_data(handle)
                cloned_handle.set_stream(handle.strid, handle.color)

                # Map the origin handle to the cloned handle:
                Handle.clone_map[handle] = cloned_handle

        # Return the cloned node:
        return cloned_node

    def resize(self, delta: int | float):
        """
        Resizes the _node in discrete steps.
        :param delta: The amount to resize the node's height. Positive values increase height, negative values decrease it.
        """

        # Set a minimum _node-height:
        if  delta < 0 and self._rect.height() < 200:
            QApplication.beep()
            return

        # Resize _node, adjust contents:
        self._rect.adjust(0, 0, 0, delta)
        self._anchor_inp.resize(delta)
        self._anchor_out.resize(delta)

        # Notify application of state-change:
        self.sig_item_updated.emit()

    @validator
    def on_anchor_clicked(self, cpos: QPointF):
        """
        Handles the event when an anchor is clicked.
        :param cpos: Position of the handle in anchor coordinates.
        """
        if  not isinstance(anchor := self.sender(), Anchor):
            logging.error("Invalid sender: Expected Anchor instance.")
            return

        if  not isinstance(cpos, QPointF):
            logging.error("Invalid position: Expected QPointF instance.")
            return

        npos   = self.mapFromItem(anchor, cpos)
        handle = self.create_handle(anchor.role, npos)
        handle.sig_item_clicked.emit()

    @validator
    def on_handle_removed(self):
        """
        This slot is triggered when a handle is removed from the node.
        :param: handle: The handle that was removed by the user.
        """
        if not isinstance(handle := self.sender(), Handle): return

        batch  = BatchActions([])

        # If the handle is connected, disconnect it:
        if  handle.connected:
            batch.add_to_batch(DisconnectHandleAction(self.scene(), handle.connector))

        batch.add_to_batch(RemoveHandleAction(self, handle))
        self.sig_exec_actions.emit(batch)

    # ------------------------------------------------------------------------------------------------------------------
    # Property Getter(s) and Setter(s)
    # Name                              Description
    # ------------------------------------------------------------------------------------------------------------------
    # uid()                             Returns the unique identifier of the node.
    # ------------------------------------------------------------------------------------------------------------------

    @property
    def uid(self):
        """
        Returns the unique identifier of the node.
        :return: str
        """
        return self._nuid.toPlainText()

    @uid.setter
    @validator
    def uid(self, value: str):
        """
        Sets the unique identifier of the node.
        :param value: The new unique identifier for the node.
        """
        self._nuid.setPlainText(value)

    @property
    def name(self) -> str:
        """
        Returns the name of the node.
        :return: str
        """
        return self._name.toPlainText()

    @name.setter
    @validator
    def name(self, value: str):
        """
        Sets the name of the node.
        :param value: The new name for the node.
        """
        self._name.setPlainText(value)
        self.sig_item_updated.emit()

    @property
    def open(self):
        """
        Returns whether the node is open (expanded).
        :return: bool
        """
        return self._open

    @open.setter
    @validator
    def open(self, flag: bool):
        """
        Sets the open state of the node.
        :param flag:
        """
        self._open = flag

    @validator
    def handle_offset(self, role: EntityRole) -> float:
        """
        Returns the offset of the node's anchor for the specified role.
        :param role: The role of the anchor (e.g., INP, OUT).
        :return: float: The x-position of the anchor in the node's coordinate system.
        """
        return -95 if role == EntityRole.INP else 95