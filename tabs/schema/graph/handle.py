import logging
import weakref

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
    QBrush,
    QColor,
    QFont,
    QPen
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
from util           import random_id, load_svg
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
            self.bg_normal  = QBrush(Qt.GlobalColor.green)
            self.bg_paired  = QBrush(QColor(0xff3a35))
            self.bg_active  = self.bg_normal

    # Initializer:
    def __init__(self,
                 _symbol: str,
                 _coords: QPointF,
                 _eclass: EntityClass,
                 _parent: QGraphicsObject | None = None):

        """
        Initialize a new handle with given entity-class, coordinates, and symbol.

        Parameters:
            _symbol (str): Symbol of the handle.
            _coords (QPointF): Coordinates of the handle.
            _eclass (EntityClass): Entity class of the handle (see `custom/entity.py`).
            _parent (QGraphicsObject, optional): Parent object of the handle (default: None).
        """

        # Validate coordinate and symbol:
        if not isinstance(_symbol, str):                        raise TypeError("Expected argument `_symbol` of type `str`")
        if not isinstance(_coords, QPointF):                    raise TypeError("Expected argument `_coords` of type `QPointF`")
        if _eclass not in [EntityClass.INP, EntityClass.OUT]:   raise ValueError("Invalid entity class")

        # Initialize base-class:
        super().__init__(_parent)

        # Display handle's symbol and customize:
        self._label = Label(self, _symbol,
                            font=QFont("Nunito", 12),
                            align=Qt.AlignmentFlag.AlignRight if _eclass == EntityClass.OUT else Qt.AlignmentFlag.AlignLeft,
                            editable=False)
        self._label.setPos(7.5 if _eclass == EntityClass.INP else -self._label.textWidth() - 7.5, -12.5)
        self._label.sig_text_changed.connect(self.rename)

        # Attrib (Must be defined after `_label`):
        self._attr = self.Attr()
        self._styl = self.Style()
        self._huid = random_id(prefix='H')

        self.offset = _coords.toPoint().x()
        self.stream = _eclass
        self.symbol = _symbol
        self.label  = _symbol

        # Connection status:
        self.connected = False
        self.conjugate = None
        self.connector = None

        # Tags:
        size = 12
        self._tags = load_svg("rss/icons/star.svg", size)
        self._tags.setTransformOriginPoint(size/2, size/2)
        self._tags.setPos(4 if self.stream == EntityClass.OUT else - 28, -12.5)
        self._tags.setParentItem(self)
        self._tags.hide()

        # Hover hint:
        self._hint = QGraphicsEllipseItem(self._attr.mark, self)
        self._hint.setBrush(Qt.GlobalColor.black)
        self._hint.setPen(QPen())
        self._hint.hide()

        # Behaviour:
        self.setPos(_coords)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Initialize menu:
        self._init_menu()

    # Context-menu initializer:
    def _init_menu(self):
        """
        Initializes the context menu for the handle.

        Parameters: None
        Returns: None
        """

        # Initialize menu:
        self._menu = QMenu()
        decision = self._menu.addAction("Decision Variable")
        decision.triggered.connect(lambda: self.set_decision(decision.isChecked()))
        decision.setCheckable(True)

        self._menu.addSeparator()
        self._subm = self._menu.addMenu("Stream")

        # Main menu actions:
        edit_action = self._menu.addAction("Edit Label")
        edit_action.triggered.connect(self.set_editable)
        edit_action.setObjectName("Edit Label")

        unpair_action = self._menu.addAction("Unpair")
        unpair_action.triggered.connect(self.unpair)
        unpair_action.setObjectName("Unpair")

        delete_action = self._menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.sig_item_removed.emit(self))

        # Sub-menu customization:
        prompt = QLineEdit()
        prompt.setPlaceholderText("Enter Category")

        action = QWidgetAction(self._subm)
        action.setDefaultWidget(prompt)

        # Add actions to sub-menu:
        self._subm.addAction(action)
        self._subm.addSeparator()

    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Returns an artifically enlarged bounding rectangle.
    # 2. paint                  Handles the painting of the handle.
    # 3. itemChange             Emits the `sig_item_shifted` signal when the handle's scene-position changes, which is
    #                           captured by the connector.
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self):
        """
        Re-implementation of `QGraphicsObject.boundingRect`. The returned rectangle is larger than the handle's actual size,
        to allow for a hover-indicator.

        Returns:
            QRectF: The bounding rectangle of the handle.
        """

        return QRectF(-2.0 * self.Attr.size, -2.0 * self.Attr.size, 4.0 * self.Attr.size, 4.0 * self.Attr.size)

    def paint(self, painter, option, widget = ...):
        painter.setPen(self._styl.pen_border)
        painter.setBrush(self._styl.bg_active)
        painter.drawEllipse(self._attr.rect)

    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.sig_item_shifted.emit(self)

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

        # Enable/disable actions based on handle's state:
        unpair = self._menu.findChild(QAction, name="Unpair")
        unpair.setEnabled(self.connected)

        # Initialize menu-actions:
        menu_actions = [
            StreamMenuAction(stream, self._strid == stream.strid)
            for stream in self.scene().type_db
        ]

        # Sort menu-actions by label:
        menu_actions.sort(key=lambda x: x.label())
            
        # Add streams dynamically to sub-menu:
        for action in menu_actions:
            self._subm.addAction(action)
            action.triggered.connect(self.on_stream_selected)
            action.setEnabled(False if self.connected and self.stream == EntityClass.INP else True)

        self._menu.popup(QCursor.pos())
        self._menu.exec()

        # Remove all QActions from the sub-menu, leave the QWidgetAction as is:
        for action in menu_actions: self._subm.removeAction(action)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self._huid)

        self._hint.show()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):

        self._hint.hide()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """
        If handle is paired, toggle-on the handle's movable-flag. Otherwise, emit the `sig_item_clicked` signal.

        Parameters:
            event (QGraphicsSceneMouseEvent): Mouse-press event, instantiated by Qt.
        """

        if event.button() == Qt.MouseButton.LeftButton:

            if  self.connected: # Toggle-on movable-flag:
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
    # 2. rename                 Rename the handle's label.
    # 3. lock                   Lock handle to a conjugate and connector.   
    # 4. free                   Free handle from its conjugate and connector.
    # 5. set_stream             Set the stream of the handle.
    # 6. set_editable           Make the handle's label temporarily editable.
    # ------------------------------------------------------------------------------------------------------------------

    def unpair(self):
        """
        Unpair this handle from its conjugate.

        Parameters: None
        Returns: None
        """

        # Emit signal to disconnect handle:
        self.sig_item_cleared.emit(self)

        # Initiate unpairing through stack-manager:
        logging.info("Unpairing handle")

    def rename(self, _label: str):
        """
        Rename the handle's label.

        Parameters:
            _label (str): The new label for the handle.
        Returns: None
        """

        self._prop["label"] = _label
        self._label.setPlainText(self.label)

    def lock(self, conjugate, connector):

        # Store references:
        self.connected = True
        self.conjugate = weakref.ref(conjugate)
        self.connector = weakref.ref(connector)

        # Change background color to red:
        self._styl.bg_active = self._styl.bg_paired

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

        # Change background color to normal:
        self._styl.bg_active = self._styl.bg_normal

        # Make item immovable again:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def on_stream_selected(self):

        # Import Canvas:
        from tabs.schema.canvas import Canvas

        # Get sender and canvas:
        _action = self.sender()
        _canvas = self.scene()

        # Validate signal-emitter:
        if (
            not isinstance(self.sender(), StreamMenuAction) or 
            not isinstance(_canvas, Canvas)
        ): 
            return

        # Get stream-id:
        _stream = _action.label()
        _stream = _canvas.find_stream(_stream)

        # Set stream:
        self.set_stream(_stream)

        # Notify application of stream-change:
        self.sig_item_updated.emit(self)

    def set_stream(self, _stream: Stream):

        # Validate input:
        if not isinstance(_stream, Stream): return

        # Set stream:
        self.strid = _stream.strid
        self.color = _stream.color

        # If handle is paired, update conjugate and connector:
        if  self.connected and self.stream == EntityClass.OUT:
            self.connector().set_color (_stream.color)
            self.conjugate().set_stream(_stream)

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

    @property
    def uid(self):  return self._huid