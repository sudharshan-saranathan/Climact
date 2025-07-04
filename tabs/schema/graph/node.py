import qtawesome as qta
import types
import dataclasses

from PyQt6.QtGui import (
    QPen,
    QFont,
    QIcon,
    QColor,
    QBrush,
    QPainter
)

from PyQt6.QtCore import (
    Qt,
    QRectF,
    QLineF,
    QPointF,
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QMenu,
    QColorDialog,
    QApplication,
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsLineItem
)

from actions import *
from custom  import *
from util    import *

from .anchor import Anchor
from .handle import Handle
from config  import ViewerConfig

# Node default configuration:
nodeDefaults = {
    "uid"           : str(),
    "name"          : "Node",
    "spos"          : QPointF(0, 0),
    "rect"          : QRectF(-100, -75, 200, 150),
    "step"          : 50,
    "inp"           : dict(),
    "out"           : dict(),
    "par"           : dict(),
    "equations"     : list(),
    "normal-border" : 0x0,
    "select-border" : 0xf99c39,
    "background"    : 0xffffff,
}

# Node class:
class Node(QGraphicsObject):

    # Signals:
    sig_exec_actions = pyqtSignal(AbstractAction)   # Emitted to execute actions and push them to the undo/redo stack.
    sig_item_updated = pyqtSignal()                 # Emitted when the node has been updated (e.g., renamed, resized, etc.).
    sig_item_removed = pyqtSignal()                 # Emitted when the user deletes the node (e.g., via context-menu).
    sig_item_clicked = pyqtSignal()                 # Emitted when the node is double-clicked.
    sig_handle_clicked = pyqtSignal(Handle)         # Emitted when a handle is clicked, signals the scene to begin a transient connection.
    sig_handle_updated = pyqtSignal(Handle)         # Emitted when a handle is updated (e.g., renamed, recategorized, etc.).
    sig_handle_removed = pyqtSignal(Handle)         # Emitted when the user deletes a handle (e.g., via context-menu).

    # Default Attributes:
    class Attr:
        def __init__(self):
            self.rect  = QRectF(-100, -75, 200, 150)        # Default rectangle size of the node.
            self.step = 50                                  # Default step-size for resizing the node.

    # Style:
    class Visual:
        def __init__(self):
            self.pen_border = QPen(QColor(0x000000), 2.0)   # Default border pen for the node.
            self.pen_select = QPen(QColor(0xf99c39), 2.0)   # Pen used when the node is selected.
            self.background = QColor(0xffffff)              # Default background color of the node.

    # Initializer:
    def __init__(self, spos: QPointF, **kwargs):

        # Initialize base-class and customize behavior:
        super().__init__(None)
        super().setAcceptHoverEvents(True)
        super().setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        # Node's properties:
        for attr in nodeDefaults:
            self.setProperty(attr,kwargs.get(attr, None) or nodeDefaults[attr])

        # Initialize style and attrib:
        self.double_clicked = False             # Used to track when the node has been double-clicked
        self._style = self.Visual()             # Instantiate the node's style
        self._nuid  = kwargs.get("uid", None)   # Unique identifier for the node, defaults to `None`.
        self._spos  = spos                      # Used to track and emit signal if the node has been moved
        self._attr  = self.Attr()               # Instantiate the node's attribute
        self._data  = dict({
            EntityClass.INP:    dict(),         # Dictionary for input variable(s)
            EntityClass.OUT:    dict(),         # Dictionary for output variable(s)
            EntityClass.PAR:    dict(),         # Dictionary for parameters
            EntityClass.EQN:    list()          # List of equations
        })

        # Label to display the node's name:
        self._title = Label(self, self.property('name'), width=120, align=Qt.AlignmentFlag.AlignCenter, editable=True)
        self._title.sig_text_changed.connect(self.sig_item_updated.emit)  # Emit signal when the title is changed
        self._title.setPos(-60, -72)

        # Header-buttons:
        expand_button = Button("rss/icons/expand.svg", self)
        shrink_button = Button("rss/icons/shrink.svg", self)
        delete_button = Button("rss/icons/delete.svg", self)

        expand_button.moveBy(70, -59)
        shrink_button.moveBy(70, -65)
        delete_button.moveBy(86, -62)

        expand_button.sig_button_clicked.connect(lambda: self.resize(self._attr.step))
        shrink_button.sig_button_clicked.connect(lambda: self.resize(-self._attr.step))
        delete_button.sig_button_clicked.connect(self.sig_item_removed.emit)

        # Instantiate anchors:
        self._anchor_inp = Anchor(EntityClass.INP, self)
        self._anchor_out = Anchor(EntityClass.OUT, self)

        # Position anchors:
        self._anchor_inp.setPos(-95, 0)
        self._anchor_out.setPos( 95, 0)

        self._anchor_inp.sig_item_clicked.connect(self.on_anchor_clicked)
        self._anchor_out.sig_item_clicked.connect(self.on_anchor_clicked)

        # Initialize menu:
        self._menu = QMenu()
        self._init_menu()

    def __getitem__(self, eclass: EntityClass):
        """
        Returns a dictionary or list depending on the entity sought:
        """

        if eclass == EntityClass.VAR:   return self._data[EntityClass.INP] | self._data[EntityClass.OUT]
        else:                           return self._data[eclass]

    def __setitem__( self,
                    _tuple: tuple,
                    _value: EntityState | str | list):
        """
        Sets the state of an entity belonging to the node.
        """

        # Resolve tuple:
        eclass, entity = _tuple

        # Assign data:
        if  eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.VAR]:
            self._data[eclass][entity] = _value

        if  eclass in [EntityClass.PAR]:
            self._data[eclass] = _value

        if  eclass == EntityClass.EQN:
            self._data[eclass] = _value

    def _init_menu(self):
        """
        Adds actions to the context menu and connects them to appropriate slots.
        """

        # Add actions to the menu:
        template_action = self._menu.addAction(qta.icon("ph.floppy-disk", color="black"), "Save to Library", lambda: print("Save to Library"))
        bg_color_action = self._menu.addAction(qta.icon("mdi.palette", color='blue'), "Set Background", self.on_set_color)

        # Additional actions:
        self._menu.addSeparator()
        shrink_action = self._menu.addAction(QIcon("rss/icons/shrink.svg"), "Shrink", lambda: self.resize(-self._attr.step))
        expand_action = self._menu.addAction(QIcon("rss/icons/expand.svg"), "Expand", lambda: self.resize(self._attr.step))

        self._menu.addSeparator()
        print_action  = self._menu.addAction("Print Info", self.on_print_info)
        delete_action = self._menu.addAction(QIcon("rss/icons/menu-delete.png"), "Delete", self.sig_item_removed.emit)

        # Make icons visible:
        template_action.setIconVisibleInMenu(True)
        bg_color_action.setIconVisibleInMenu(True)

        expand_action.setIconVisibleInMenu(True)
        shrink_action.setIconVisibleInMenu(True)
        delete_action.setIconVisibleInMenu(True)

    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Implementation of QGraphicsObject.boundingRect() (see Qt documentation).
    # 2. paint                  Implementation of QGraphicsObject.paint() (see Qt documentation).
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self):
        # Return bounding-rectangle:
        return self._attr.rect

    def paint(self, painter, option, widget = ...):
        """
        Re-implementation of QGraphicsObject.paint().

        :param painter: QPainter instance used to draw the node.
        :param option:  Painting options, managed by Qt.
        :param widget:  Optional widget to paint on, defaults to `...` (not used here).
        """

        # Select different pens for selected and unselected states:
        pen = self._style.pen_select if self.isSelected() else self._style.pen_border
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Enable antialiasing for smoother edges
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(self._style.background)))
        painter.drawRoundedRect(self._attr.rect, 8, 8)

        painter.setPen(QPen(Qt.GlobalColor.lightGray, 1.0))
        painter.drawText(QPointF(-90, -56, ), self._nuid)

        # Draw the separators:
        pen = QPen(Qt.GlobalColor.black, 1.0)
        painter.setPen(pen)
        painter.drawLine(QPointF(-98, -48), QPointF(98, -48))                                    # Top separator

        pen = QPen(Qt.GlobalColor.gray, 0.5)
        painter.setPen(pen)
        painter.drawLine(QPointF(0, -46), QPointF(0, self._attr.rect.bottom() - 2))              # Vertical separator

    def itemChange(self, change, value):

        # Import canvas module:
        from tabs.schema import CanvasState

        # If this node has been added to a canvas:
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged and value:

            # Connect node's signals to the canvas's slots:
            self.sig_item_updated.connect(lambda: value.sig_canvas_state.emit(CanvasState.HAS_UNSAVED_CHANGES))
            self.sig_item_removed.connect(value.on_item_removed)
            self.sig_item_clicked.connect(value.sig_node_clicked.emit)

            # Connect signal-exec actions:
            self.sig_exec_actions.connect(lambda: value.sig_canvas_state.emit(CanvasState.HAS_UNSAVED_CHANGES))
            self.sig_exec_actions.connect(value.manager.do)

            # Forward handle's signals:
            self.sig_handle_clicked.connect(value.begin_transient)

            # Adjust scene-position:
            self.setPos(self._spos)

        return value

    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. hoverEnterEvent        Triggered when the mouse enters the node.
    # 2. hoverLeaveEvent        Triggered when the mouse leaves the node.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Triggered when the context menu is requested.

        :param event: Context menu event, triggered and managed by Qt.
        """

        # Forward event to super-class:
        super().contextMenuEvent(event)
        if event.isAccepted(): return

        # Display context menu:
        self.setSelected(True)
        self._menu.exec(event.screenPos())
        event.accept()

    def hoverEnterEvent(self, event):
        """
        Triggered when the mouse enters the node.

        Args:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.
        """
        super().hoverEnterEvent(event)              # Forward to super-class
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Set arrow-cursor
    
    def hoverLeaveEvent(self, event):
        """
        Triggered when the mouse leaves the node.

        Args:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.
        """
        super().hoverLeaveEvent(event)              # Forward to super-class
        self.unsetCursor()                          # Unset cursor

    def mouseReleaseEvent(self, event):
        """
        Triggered when the mouse is released.

        Args:
            event (QMouseEvent) : Mouse event, instantiated by Qt.
        """

        # Forward event to super-class:
        super().mouseReleaseEvent(event)
        
        # If the node has been moved, notify canvas:
        if  self.scenePos() != self._spos:
            self.sig_item_updated.emit()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked = True
        self.sig_item_clicked.emit()  # Emit signal when the node is double-clicked

    # User-defined methods ---------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. clone                  Duplicates the node.
    # 2. resize                 Resizes the node in discrete steps.
    # 3. create_handle          Creates a new handle.
    # 4. create_huid            Creates a unique identifier for each handle.
    # 5. on_anchor_clicked      Triggered when an anchor is clicked.
    # 6. on_handle_clicked      Triggered when a handle is clicked.
    # 7. on_handle_updated      Triggered when a handle is updated.
    # 8. on_handle_removed      Triggered when a handle is removed.
    # ------------------------------------------------------------------------------------------------------------------

    # Return transformed equations:
    def substituted(self) -> list[str]:

        transformed = list()
        node_prefix = self.uid

        variables = [
            variable for variable, state in self[EntityClass.VAR].items()
            if state == EntityState.ACTIVE
        ]

        parameters = [
            parameter for parameter, state in self[EntityClass.PAR].items()
            if state == EntityState.ACTIVE
        ]

        equations = self._data[EntityClass.EQN].copy()

        # Create a dictionary of symbol-replacements:
        replacements  = dict()

        # Variable symbols (R00, P00, ...) are replaced with connector symbols (X0, X1, ...)
        for var in variables:
            replacements[var.symbol] = var.connector().symbol if var.connected else None

        # Parameter-symbols are prefixed with the node's UID:
        for par in parameters:
            replacements[par.symbol] = f"{node_prefix}_{par.symbol}"

        # Modify all equations:
        for equation in equations:
            tokens = equation.split(' ')
            update = [replacements.get(token, token) for token in tokens]

            if not None in update:
                transformed.append(str(" ").join(update))

        return transformed

    def clone(self, **kwargs):
        """
        Create an identical copy of this node.

        Returns:
            Node: A new node with the same properties as the original node.
        """

        # Instantiate a new node:
        node = Node(self.scenePos() + QPointF(25, 25))
        node.setParentItem(self.parentItem())

        # Adjust node-height:
        diff = self.boundingRect().height() - node.boundingRect().height()
        node.resize(diff)
        node.setSelected(self.isSelected())

        # Construct lists of active data:
        active_vars = [_variable  for _variable , _state in self[EntityClass.VAR].items() if _state == EntityState.ACTIVE]
        active_pars = [_parameter for _parameter, _state in self[EntityClass.PAR].items() if _state == EntityState.ACTIVE]

        # Copy this node's variable(s):
        for  entity in active_vars:

            # Instantiate new handle and copy attribute(s):
            copied = node.create_handle(entity.eclass,entity.pos())
            entity.clone_into(copied)

            # Add copied variable to the node's registry:
            node[entity.eclass][copied] = EntityState.ACTIVE
            Handle.cmap[entity] = copied

        # Copy this node's parameter(s):
        for entity in active_pars:
            copied = Entity()              # Instantiate a new entity
            entity.clone_into(copied)     # Copy attributes into the new entity

            # Add copied variable to the node's registry:
            node[entity.eclass][copied] = EntityState.ACTIVE

        # Deselect this node:
        self.setSelected(False)

        # Process keyword-args:
        if "set_uid" in kwargs: node.uid = kwargs.get("set_uid")

        # Return reference to the created node:
        return node

    def resize(self, delta: int | float):
        """
        Resizes the node in discrete steps.

        :param delta: The amount by which to resize the node. Positive values increase the height, negative values decrease it.
        """

        # Set a minimum node-height:
        if delta < 0 and self._attr.rect.height() < 200:
            QApplication.beep()
            return

        # Resize node, adjust contents:
        self._attr.rect.adjust(0, 0, 0, delta)
        self._anchor_inp.resize(delta)
        self._anchor_out.resize(delta)
        self.update()

        # Notify application of state-change:
        self.sig_item_updated.emit()

    def symbols(self) -> list:

        _symbols = list()
        for _entity, _state in self[EntityClass.VAR].items():
            if  _state == EntityState.ACTIVE:
                _symbols.append(_entity.symbol)

        for _entity, _state in self[EntityClass.PAR].items():
            if  _state == EntityState.ACTIVE:
                _symbols.append(_entity.symbol) 

        return _symbols

    def replace(self, _oldsym: str, _newsym: str):
        """
        Replaces `_oldsym` with `_newsym` in the node's equations. This method is called when a symbol is renamed (e.g.,
        when a parameter is renamed or when a variable's symbols are changed due to being imported into a non-empty
        canvas).

        :param: _oldsym (str): The old symbol to be replaced.
        :param: _newsym (str): The new symbol to replace the old one with
        """

        # Replace old symbol with new symbol in equations:
        for i, equation in enumerate(self._data[EntityClass.EQN]):
            if _oldsym in equation:
                self._data[EntityClass.EQN][i] = equation.replace(_oldsym, _newsym)

    def create_handle(self,
                      _eclass: EntityClass,
                      _coords: QPointF,
                      _clone : Handle = None
                      ):
        """
        Creates a new handle at the given coordinate, returns reference to the handle.

        Args:
            _eclass (EntityClass): The stream-direction of the new handle (INP or OUT).
            _coords (QPointF)    : The coordinates of the new handle (must be in the node's coordinate-system).
            _clone (Handle)      : If provided, the created handle will be a clone of this handle

        Returns:
            Handle: Reference to the new handle.
        """

        # Instantiate a new handle:
        handle = Handle(_eclass,
                         _coords,
                         self.create_huid(_eclass),
                         self
                        )

        # Connect handle's signals to the node's slots:
        handle.sig_item_clicked.connect(self.sig_handle_clicked.emit)
        handle.sig_item_updated.connect(self.sig_handle_updated.emit)
        handle.sig_item_cleared.connect(self.on_handle_cleared)
        handle.sig_item_removed.connect(self.on_handle_removed)
        handle.sig_item_updated.connect(self.sig_item_updated.emit)

        # Add the handle to the node's database:
        self[_eclass][handle] = EntityState.ACTIVE

        # Return reference to handle:
        return handle

    def create_huid(self, _eclass: EntityClass):
        """
        Creates a unique identifier for each handle.

        Returns:
            str: The unique identifier for the handle.
        """

        # Create a unique handle-identifier:
        prefix = "P" if _eclass == EntityClass.OUT else "R"
        id_set = {
            int(handle.symbol[1:])         # Get the node's currently used symbols
            for handle, state in self[_eclass].items()
            if  state
        }

        # If `id_set` is empty, return prefix + "00":
        if not id_set:  return prefix + "00"

        # Get sequence of integers from 0 to `max(id_set) + 1`, not in `id_set`:
        sequence = set(range(0, max(id_set) + 2))
        reusable = sequence - id_set

        # Return UID (prefix + smallest integer not in `id_set`):
        return prefix + str(min(reusable)).zfill(2)

    # Triggered when an anchor is clicked:
    def on_anchor_clicked(self, coords: QPointF):
        """
        Triggered when an anchor is clicked.

        :param: _coords (QPointF): The coordinates where the anchor was clicked, in scene-coordinates.
        """

        # Get the anchor that was clicked:
        anchor = self.sender()
        eclass = anchor.stream()

        # Create a new handle at the anchor's position:
        coords = self.mapFromItem(anchor, coords)        # Map coordinate to node's coordinate-system
        handle = self.create_handle(eclass, coords)
        handle.sig_item_clicked.emit(handle)              # Emit signal to begin transient-connection.

        # Enter the handle into the node's database:
        self[eclass, handle] = EntityState.ACTIVE         # Set state `EntityState.ACTIVE`

        # Notify application of state-change:
        self.sig_exec_actions.emit(CreateHandleAction(self, handle))
        self.sig_item_updated.emit()
    
    # Triggered when a handle is removed:
    def on_handle_removed(self, _handle: Handle):
        # Create an undoable remove-action and notify the actions-manager:
        self.sig_exec_actions.emit(RemoveHandleAction(self, _handle))

    # Triggered when a handle is cleared:
    def on_handle_cleared(self, handle: Handle):
        
        # Create an undoable disconnect-action:
        _action = DisconnectHandleAction(self.scene(), handle.connector())

        # Emit signal to disconnect handle:
        self.sig_exec_actions.emit(_action)

    # Change background color:
    def on_set_color(self, color: QColor | None = None):
        color = color or QColorDialog.getColor(self._style.background, None, "Select Background Color")
        self._style.background = color if color.isValid() else self._style.background

    def on_print_info(self):
        for item in self._data[EntityClass.INP]:
            print(f"Input: {item.symbol} {item.isVisible()} ({self._data[EntityClass.INP][item]})")

        for item in self._data[EntityClass.OUT]:
            print(f"Input: {item.symbol} {item.isVisible()} ({self._data[EntityClass.OUT][item]})")

    # Properties -------------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. uid                   The node's unique identifier.
    # 2. name                  The node's name.
    # ------------------------------------------------------------------------------------------------------------------
    
    @property
    def uid(self):  return self._nuid
    
    @property
    def title(self): return self._title.toPlainText()

    @uid.setter
    def uid(self, value: str):
        self._nuid = value

    @title.setter
    def title(self, value: str):
        self._title.setPlainText(value)
