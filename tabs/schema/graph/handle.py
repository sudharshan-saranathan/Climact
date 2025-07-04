import logging
import weakref

import qtawesome
from PyQt6.QtCore import (
    pyqtSignal,
    QPointF,
    QRectF,
    Qt
    )

from PyQt6.QtGui import (
    QTextCursor,
    QAction,
    QCursor,
    QPixmap,
    QBrush,
    QColor,
    QFont,
    QPen, QPainter
)

from PyQt6.QtWidgets import (
    QGraphicsObject,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QWidgetAction,
    QLineEdit,
    QMenu,
    )

from dataclasses    import dataclass
from util import random_id, load_svg, random_hex, anti_color
from custom         import *

class Handle(QGraphicsObject, Entity):

    # Signals:
    sig_item_clicked = pyqtSignal(QGraphicsObject)
    sig_item_updated = pyqtSignal(QGraphicsObject)
    sig_item_shifted = pyqtSignal(QGraphicsObject)
    sig_item_removed = pyqtSignal(QGraphicsObject)
    sig_item_cleared = pyqtSignal(QGraphicsObject)

    # Copy map:
    cmap = {}

    @dataclass
    class Attr:
        size = 5.0
        rect = QRectF(-size/2.0, -size/2.0, size, size)
        mark = QRectF(-1.0, -1.0, 2.0, 2.0)

    @dataclass
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.black, 1.0)
            self.bg_normal  = QBrush(QColor(0xcfffb3))
            self.bg_paired  = QBrush(QColor(0xff3a35))
            self.bg_active  = self.bg_normal

    # Initializer:
    def __init__(self,
                 eclass: EntityClass,
                 coords: QPointF,
                 symbol: str,
                 parent: QGraphicsObject | None = None):

        # Initialize base-class and customize behavior:
        super().__init__(parent)
        super().setPos(coords)
        super().setAcceptHoverEvents(True)
        super().setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Display handle's symbol and customize:
        self._label = Label(self, symbol,
                            align=Qt.AlignmentFlag.AlignRight if eclass == EntityClass.OUT else Qt.AlignmentFlag.AlignLeft,
                            editable=False)

        self._label.setPos(7.5 if eclass == EntityClass.INP else -self._label.textWidth() - 7.5, -12.5)
        self._label.sig_text_changed.connect(self.rename)

        # Attrib (Must be defined after `_label`):
        self._attr = self.Attr()
        self._styl = self.Style()
        self._huid = random_id(prefix='H')

        self.contrast = False # Flag to determine whether the handle's text-color should contrast its stream-color
        self.offset = coords.toPoint().x()
        self.eclass = eclass
        self.symbol = symbol
        self.label  = symbol

        # Connection status:
        self.connected = False
        self.conjugate = None
        self.connector = None

        # Tags:
        size = 12
        self._tags = load_svg("rss/icons/star.svg", size)
        self._tags.setTransformOriginPoint(size/2, size/2)
        self._tags.setPos(4 if self.eclass == EntityClass.OUT else - 28, -12.5)
        self._tags.setParentItem(self)
        self._tags.hide()

        # Hover hint:
        self._hover  = False
        self._cursor = QCursor(QPixmap("rss/icons/click.svg").scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation), -1, -1)

        # Initialize menu:
        self._init_menu()

    # Context-menu initializer:
    def _init_menu(self):
        """
        Initializes the context menu for the handle.
        """

        # Initialize menu:
        self._menu = QMenu()
        decision = self._menu.addAction("Decision Variable", lambda: self.set_decision(decision.isChecked()))
        decision.setCheckable(True)

        self._menu.addSeparator()
        self._subm = self._menu.addMenu("Stream")

        # Main menu actions:
        edit_action   = self._menu.addAction(qtawesome.icon("ph.pencil-simple", color='black'), "Edit Label", self.set_editable)
        unpair_action = self._menu.addAction(qtawesome.icon("ph.eject", color="green"), "Unpair", self.unpair)
        delete_action = self._menu.addAction(qtawesome.icon("ph.trash", color="red"), "Delete", lambda: self.sig_item_removed.emit(self))

        edit_action.setIconVisibleInMenu(True)
        delete_action.setIconVisibleInMenu(True)
        unpair_action.setIconVisibleInMenu(True)
        unpair_action.setObjectName("Unpair")

        # Sub-menu customization:
        widget = QLineEdit()
        widget.setPlaceholderText("Enter Category")
        widget.returnPressed.connect(lambda: self.create_stream(widget.text()))

        self._prompt = QWidgetAction(self._subm)
        self._prompt.setDefaultWidget(widget)
        self._prompt.setObjectName("Prompt")

        # Add actions to the submenu:
        self._subm.addAction(self._prompt)
        self._subm.addSeparator()

    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Returns an artificially enlarged bounding rectangle.
    # 2. paint                  Handles the painting of the handle.
    # 3. itemChange             Emits the `sig_item_shifted` signal when the handle's scene-position changes, which is
    #                           captured by the connector.
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self):
        """
        Re-implementation of `QGraphicsObject.boundingRect`. The returned rectangle is larger than the handle's actual size,
        to allow for a hover-indicator.
        """
        return QRectF(-self.Attr.size, -self.Attr.size, 2.0 * self.Attr.size, 2.0 * self.Attr.size)

    def paint(self, painter, option, widget = ...):
        """
        Re-implementation of `QGraphicsObject.paint`. This method is responsible for drawing the handle on the canvas.
        :param painter:
        :param option:
        :param widget:
        :return:
        """

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._styl.pen_border)
        painter.setBrush(self._styl.bg_active)
        painter.drawEllipse(self._attr.rect)

        if  self._hover:
            painter.setBrush(QBrush(0x0))
            painter.drawEllipse(QRectF(-0.75, -0.75, 1.5, 1.5))

    def itemChange(self, change, value):

        # If the handle was moved, redraw the connector:
        handle_moved = QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged
        if  change == handle_moved and self.connected:
            self.connector().redraw()

        return value
    
    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. contextMenuEvent       Handles context-menu events (triggered when the user right-clicks on the handle).
    # 2. hoverEnterEvent        Show a hover-indicator when the mouse is over the handle.
    # 3. hoverLeaveEvent        Hide the hover-indicator when the mouse is no longer over the handle.
    # 4. mousePressEvent        For unpaired handles, this will emit a signal to begin a transient-connection. For
    #                           paired handles, this will toggle-on the handle's movable-flag.
    # 5. mouseReleaseEvent      Toggles off the handle's movable-flag, snaps x-position to the offset value.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):

        # Enable/disable actions based on the handle's state:
        unpair = self._menu.findChild(QAction, name="Unpair")
        unpair.setEnabled(self.connected)

        # Initialize menu-actions and sort them:
        menu_actions = [StreamMenuAction(stream, self.strid == stream.strid) for stream in self.scene().type_db]
        menu_actions.sort(key=lambda x: x.label)
            
        # Add streams dynamically to the submenu:
        for action in menu_actions:
            self._subm.addAction(action)
            action.triggered.connect(self.on_stream_selected)
            action.setEnabled(False if self.connected and self.eclass == EntityClass.INP else True)

        self._menu.popup(QCursor.pos())
        self._menu.exec()

        # Remove all QActions from the submenu, leave the QWidgetAction as is:
        for action in menu_actions: self._subm.removeAction(action)

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setCursor(Qt.CursorShape.SizeAllCursor if self.connected else Qt.CursorShape.PointingHandCursor)
        self._hover = True

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.unsetCursor()
        self._hover = False

    def mousePressEvent(self, event):
        """
        If the handle is paired, toggle-on the handle's movable-flag. Otherwise, emit the `sig_item_clicked` signal.
        """
        from tabs.schema.graph.terminal import StreamTerminal

        # First, clear selections in the scene:
        self.scene().clearSelection()

        # If the left mouse button is pressed:
        if event.button() == Qt.MouseButton.LeftButton:

            if  self.connected: # Toggle-on movable-flag:
                if not isinstance(self.parentItem(), StreamTerminal):
                    self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

            else: # Emit signal to begin transient-connection:
                self.sig_item_clicked.emit(self)

        # Forward event to super-class:
        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        """
        Toggle off the handle's movable-flag, snap x-position to the offset value.

        Parameters:
            event (QGraphicsSceneMouseEvent): Mouse-release event, instantiated by Qt.
        """

        # Modify handle-behavior and attributes:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setPos(self.offset, self.pos().y())

        # Forward event to super-class:
        super().mouseReleaseEvent(event)

    # Custom methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. unpair                 Unpair this handle from its conjugate.
    # 5. set_stream             Set the stream of the handle.
    # 6. set_editable           Make the handle's label temporarily editable.
    # ------------------------------------------------------------------------------------------------------------------

    def clone_into(self, copied, **kwargs):

        # Call super-class implementation:
        super().clone_into(copied)

        # Set additional attribute(s):
        copied.contrast = self.contrast
        copied.offset   = self.offset

        # Set attribute(s):
        copied.rename(self.label)
        copied.sig_item_updated.emit(copied)

        if 'exclude' in kwargs and 'position' in kwargs.get('exclude'):
            return

        else:
            copied.setPos(self.pos())

    def unpair(self):
        """
        Unpair this handle from its conjugate.

        Parameters: None
        Returns: None
        """

        # Emit signal to disconnect handle:
        self.sig_item_cleared.emit(self)
        self.sig_item_updated.emit(self)

        # Initiate unpairing through stack-manager:
        logging.info("Unpairing handle")

    def rename(self, label: str):
        """
        Rename the handle's label.

        Parameters:
            label (str): The new label for the handle.
        Returns: None
        """

        self._prop["label"] = label
        self._label.setPlainText(self.label)
        self.sig_item_updated.emit(self)

        if (
            self.conjugate and
            self.eclass == EntityClass.OUT
        ):
            self.conjugate().rename(self.label)
            self.conjugate().sig_item_updated.emit(self.conjugate())

    def pair(self, conjugate: 'Handle', connector: 'Connector'):

        # Store reference(s) and
        self.connected = conjugate is not None and connector is not None
        self.conjugate = weakref.ref(conjugate)
        self.connector = weakref.ref(connector)

        # Modify appearance based on pairing-state:
        self._styl.bg_active = self._styl.bg_paired if self.connected else self._styl.bg_normal

    def lock(self, conjugate, connector):

        # Store references:
        self.connected = True
        self.conjugate = weakref.ref(conjugate)
        self.connector = weakref.ref(connector)

        # Change the background color to red:
        self._styl.bg_active = QColor(self.color)
        self.sig_item_updated.emit(self)

    def free(self, delete_connector = False):

        # If `delete` is True, delete connector:
        if (
            delete_connector and
            self.connected and
            self.connector()
        ):
            self.connector().deleteLater()

        # Toggle reference(s):
        self.connected = False
        self.conjugate = None
        self.connector = None

        # Change the background color to normal:
        self._styl.bg_active = self._styl.bg_normal

        # Make item immovable again:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.sig_item_updated.emit(self)

    def on_stream_selected(self):

        # Import Canvas:
        from tabs.schema.canvas import Canvas

        # Get stream-id:
        action = self.sender()
        canvas = self.scene()

        stream = action.label
        stream = canvas.find_stream(stream, create = True)      # Find the stream, create a new one if it doesn't exist.

        # Set stream:
        self.set_stream(stream)

    def set_stream(self, stream: Stream):

        # Set stream:
        self.strid = stream.strid
        self.color = stream.color

        # Change the color only if the `contrast` flag is set:
        if self.contrast:   self._label.setDefaultTextColor(anti_color(self.color))

        # If the handle is paired, update conjugate and connector:
        if  self.connected and self.eclass == EntityClass.OUT:
            self.connector().set_color (stream.color)
            self.conjugate().set_stream(stream)

        # Notify application of stream-change:
        self._styl.bg_active = stream.color
        self.sig_item_updated.emit(self)

    def set_editable(self):

        # Make the label temporarily editable:
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._label.setFocus(Qt.FocusReason.OtherFocusReason)

        # Highlight the entire word:
        cursor = self._label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        self._label.setTextCursor(cursor)

    def set_decision(self, _flag: bool):    
        self._tags.setVisible(_flag)

    def create_stream(self, _strid: str):

        # Import canvas module:
        from tabs.schema import Canvas

        # Define convenience variable:
        _canvas = self.scene()

        # Fetch stream:
        _stream = _canvas.find_stream(_strid, True)         # This method will also add the stream to the database
 
        # Set stream:
        self.set_stream(_stream)

        # If the menu is open, update the submenu:
        if  self._menu.isVisible(): self._menu.close()

    @property
    def uid(self):  return self._huid