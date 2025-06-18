"""
handle.py
"""

import types
import weakref
import qtawesome as qta

# PyQt6 Library:
from PyQt6.QtCore import (
    Qt,
    QRectF,
    pyqtSignal
)
from PyQt6.QtGui import (
    QPen,
    QColor,
    QCursor,
    QTextCursor
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject, QGraphicsEllipseItem, QMenu, QWidgetAction, QLineEdit
)

# Climact submodule(s):
from custom import String, StreamMenuAction
from custom.configure import EntityConfigure
from custom.entity import *
from util import anti_color

# Class Handle:
class Handle(Entity, QGraphicsObject):
    """
    This class inherits from `QGraphicsObject` and `Entity` and is a visual representation of input or output variables
    in a node.
    """
    # Signals:
    sig_item_clicked  = pyqtSignal()
    sig_item_updated  = pyqtSignal()
    sig_item_removed  = pyqtSignal()
    sig_create_stream = pyqtSignal(str)  # Signal to create a stream with a given category

    # Application-wide dictionary to map copied and cloned handles (needed to copy-paste connections as well):
    clone_map = {}

    # Visual attributes:
    @dataclasses.dataclass
    class Visual:
        """
        A dataclass to hold visual attributes of the handle.
        """
        hint_rect : QRectF = dataclasses.field(default_factory = lambda: QRectF(-1.0, -1.0, 2.0, 2.0))
        hint_color: QColor = dataclasses.field(default_factory = lambda: QColor(0x0))
        pen_normal: QPen   = dataclasses.field(default_factory = lambda: QPen(0x0))
        background: QColor = dataclasses.field(default_factory = lambda: QColor(0xcfffb3))

    # Class constructor:
    def __init__(self,
                 role:   EntityRole,
                 symbol: str,
                 strid : str,
                 parent: QGraphicsItem | None = None):

        # Initialize the Entity base-class:
        super().__init__(EntityClass.VAR, symbol, strid)

        # Initialize Entity-attribute(s):
        self.label  = symbol
        self.symbol = symbol
        self.strid  = strid
        self.eclass = EntityClass.VAR

        # Attribute(s):
        self._attr   = types.SimpleNamespace(
            rect     = QRectF(-2.5, -2.5, 5, 5),  # Bounding rectangle of the handle
            role     = role,                      # EntityRole of the handle (input or output)
            offset   = float(),                   # Fixed x-coordinate of the handle (w.r.t the node)
            movable  = True,                      # If this handle is movable (different for nodes and terminals)
            contrast = False,                     # If the text color should contrast with the background.
        )

        # Connection state:
        self._visual    = self.Visual()  # Visual attributes
        self._connected = False
        self._conjugate = None
        self._connector = None
        self._settings  = EntityConfigure(self)  # Configuration dialog for the handle

        # Label:
        self._label = String(
            self,
            symbol,
            align = Qt.AlignmentFlag.AlignLeft if role == EntityRole.INP else Qt.AlignmentFlag.AlignRight,
            editable = False
        )
        self._label.setPos(7.5 if role == EntityRole.INP else -7.5 - self._label.textWidth(), -12.0)  # Offset the label position
        self._label.sig_text_changed.connect(self.rename)

        # Hint that is shown when the handle is hovered over:
        self._hint = QGraphicsEllipseItem(self._visual.hint_rect, self)
        self._hint.setPen  (self._visual.pen_normal)
        self._hint.setBrush(self._visual.hint_color)
        self._hint.hide()

        # Customize behavior:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.setParentItem(parent)
        self._init_menu()

    # Context-menu:
    def _init_menu(self):
        """
        Initialize the context menu for the handle.
        :return:
        """
        self._menu = QMenu()
        self._subm = self._menu.addMenu('Stream')

        edit = self._menu.addAction(qta.icon('mdi.label', color='darkblue'), 'Edit', self.set_editable)
        self._menu.addSeparator()

        config = self._menu.addAction(qta.icon('ph.gear', color='black'), "Configure")
        unpair = self._menu.addAction(qta.icon('ph.eject', color='darkgreen'), 'Unpair', lambda: print('Unpair clicked'))
        remove = self._menu.addAction(qta.icon('ph.trash-simple', color='darkred'), 'Delete', lambda: self.sig_item_removed.emit())

        edit.setIconVisibleInMenu(True)
        config.setIconVisibleInMenu(True)
        unpair.setIconVisibleInMenu(True)
        remove.setIconVisibleInMenu(True)

        # Sub-menu customization:
        widget = QLineEdit()
        widget.setPlaceholderText("Enter Category")

        self._prompt = QWidgetAction(self._subm)
        self._prompt.setDefaultWidget(widget)
        self._prompt.setObjectName("Prompt")

        # Add actions to the submenu:
        self._subm.addAction(self._prompt)
        self._subm.addSeparator()

    def boundingRect(self) -> QRectF:
        """
        Return the bounding rectangle of the handle.
        """
        return self._attr.rect.adjusted(-7.5, -7.5, 7.5, 7.5)

    def paint(self, painter, option, widget=None):
        """
        Paint the handle with the specified pen and background color.
        """
        painter.setPen(self._visual.pen_normal)
        painter.setBrush(self._visual.background)
        painter.drawEllipse(self._attr.rect)

    def itemChange(self, change, value):
        """
        Emits signals when the handle is moved.
        :param change:
        :param value:
        :return:
        """
        # If the handle is connected, redraw the connector when the scene-coordinate changes:
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged and
            self._connected
        ):
            self._connector().render()

        return value

    # ------------------------------------------------------------------------------------------------------------------
    # Event handlers:
    # Name                  Description
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Handle context menu event to show the handle's context menu.
        :param event: QContextMenuEvent
        """
        # Enable/disable actions based on the handle's state:
        # unpair = self._menu.findChild(QAction, name="Unpair")
        # unpair.setEnabled(self.connected)

        # Initialize menu-actions:
        menu_actions = [
            StreamMenuAction(strid, color, self.strid == strid)
            for strid, color in self.scene().db.kind.items()
        ]

        # Sort menu-actions by label:
        menu_actions.sort(key=lambda x: x.label)

        # Add streams dynamically to the submenu:
        for action in menu_actions:
            self._subm.addAction(action)
            action.triggered.connect(self.on_stream_selected)
            action.setEnabled(False if self.connected and self.role == EntityRole.INP else True)

        self._menu.popup(QCursor.pos())
        self._menu.exec()

        # Remove all QActions from the submenu, leave the QWidgetAction as is:
        for action in menu_actions: self._subm.removeAction(action)

    def hoverEnterEvent(self, event):
        """
        Handle hover enter event to show the hint and change the cursor.
        :param event: QHoverEvent
        """
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hint.show()

        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        Handle hover leave event to hide the hint and reset the cursor.
        :param event:
        """
        # Reset the cursor and hide the hint:
        self.unsetCursor()
        self._hint.hide()

        # Call the base class implementation:
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """
        Handle mouse press event to emit a signal when the handle is clicked.
        :param event: QMouseEvent
        """
        if  not self._connected:
            self.sig_item_clicked.emit()

        elif self.movable:
             self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event to reset the movable flag.
        :param event:
        :return:
        """
        # Make the handle immovable after releasing the mouse button:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setPos (self.parentItem().handle_offset(self.role), self.pos().y())               # Reset x-coordinate to offset-position

        # Call the base class implementation:
        super().mouseReleaseEvent(event)

    # TODO: Describe user-defined functions.
    #

    # Rename the handle:
    def rename(self, text: str):
        """
        Rename the handle with the given text.
        :param text: str
        """
        self._meta.label = text
        self._label.setPlainText(text)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        if (
            self._connected and
            self._conjugate() and
            self._attr.role == EntityRole.OUT
        ):
            self._conjugate().rename(self.label)

    # Configure the handle's data:
    def configure(self):
        """
        Configure the handle's data.
        This method is a placeholder and should be implemented in subclasses.
        """
        self._settings.open()

    def toggle_state(self, connector, conjugate):
        """
        Toggle the state of the handle, either connecting or disconnecting it from a connector.
        :param connector: The connector with which this handle is connected.
        :param conjugate: The conjugate handle to this.
        :return:
        """
        from tabs.schema.graph.connector import Connector

        # Type-check:
        if (
            not isinstance(connector, Connector | None) or
            not isinstance(conjugate, Handle | None)
        ):
            raise TypeError("Invalid arguments")

        # Connect or disconnect the handle:
        if  connector and conjugate:
            self._connected = True
            self._connector = weakref.ref(connector)
            self._conjugate = weakref.ref(conjugate)
            self._visual.background = QColor(Qt.GlobalColor.darkRed)

        else:
            self._connected = False
            self._connector = None
            self._conjugate = None
            self._visual.background = QColor(0xcfffb3)  # Reset to default color

    def on_stream_selected(self):
        """
        Handle the selection of a stream from the context menu.
        :return:
        """
        # Get the action that triggered the signal:
        action = self.sender()
        canvas = self.scene()

        # Set the chosen stream:
        self.set_stream(action.label, canvas.db.kind[action.label])

    @validator
    def set_stream(self, strid: str, color: QColor):
        """
        Set the stream for the handle and update its visual attributes.
        :param strid: str
        :param color: QColor
        """
        # Set stream:
        self.strid = strid

        if  self.contrast:
            self._label.setDefaultTextColor(anti_color(color))

        # If the handle is connected, update the conjugate's stream as well:
        if (
            self.connector and
            self.conjugate and
            self.role == EntityRole.OUT
        ):
            self.connector.color = color
            self.conjugate.set_stream(strid, color)

        # Notify application of stream-change:
        self.update()
        self.sig_item_updated.emit()

    def set_editable(self):
        """
        Set the label of the handle to be editable and highlight the entire text.
        :return:
        """
        # Make the label temporarily editable:
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._label.setFocus(Qt.FocusReason.OtherFocusReason)

        # Highlight the entire word:
        cursor = self._label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        self._label.setTextCursor(cursor)

    # TODO: Describe property setters and getters.
    #
    #

    @property
    def role(self):
        """
        Return the role of the handle (input or output).
        :return: EntityRole
        """
        return self._attr.role

    @property
    def color(self):
        """
        Returns the color of the handle
        :return:
        """
        return self.scene().db.kind[self.strid]

    @property
    def movable(self) -> bool:
        """
        Return whether the handle is movable.
        :return: bool
        """
        return self._attr.movable

    @property
    def contrast(self):
        """
        Return whether the text color should contrast with the background.
        :return: bool
        """
        return self._attr.contrast

    @property
    def connected(self):
        """
        Return whether the handle is connected to a connector.
        :return: bool
        """
        return self._connected

    @property
    def conjugate(self):
        """
        Return the conjugate handle if connected.
        :return: Handle | None
        """
        return self._conjugate() if self._conjugate else None

    @property
    def connector(self):
        """
        Return the connector if connected.
        :return: Connector | None
        """
        return self._connector() if self._connector else None

    @movable.setter
    def movable(self, value: bool):
        """
        Set whether the handle is movable.
        :param value: bool
        """
        self._attr.movable = value

    @contrast.setter
    @validator
    def contrast(self, value: bool):
        """
        Set whether the text color should contrast with the background.
        :param value: bool
        """
        self._attr.contrast = value