from PyQt6.QtGui import (
    QPen,
    QIcon,
    QColor, 
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
    QGraphicsItem, 
    QGraphicsObject, 
    QGraphicsLineItem
)
from actions import *
from custom  import *
from util    import *

from .anchor import Anchor
from .handle import Handle

class Node(QGraphicsObject):
    """
    """

    # Signals:
    sig_exec_actions = pyqtSignal(AbstractAction)   # Emitted to execute actions and push them to the undo/redo stack.
    sig_item_updated = pyqtSignal()         # Emitted when the node has been updated (e.g., renamed, resized, etc.).
    sig_item_removed = pyqtSignal()         # Emitted when the user deletes the node (e.g., via context-menu).
    sig_handle_clicked = pyqtSignal(Handle) # Emitted when a handle is clicked, signals the scene to begin a transient connection.
    sig_handle_updated = pyqtSignal(Handle) # Emitted when a handle is updated (e.g., renamed, recategorized, etc.).
    sig_handle_removed = pyqtSignal(Handle) # Emitted when the user deletes a handle (e.g., via context-menu).

    # Default Attributes:
    class Attr:
        def __init__(self):
            self.rect  = QRectF(-100, -75, 200, 150)    # Default rectangle size of the node.
            self.delta = 50                             # Default step-size for resizing the node.

    # Style:
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.black, 2.0)   # Default border pen for the node.
            self.pen_select = QPen(QColor(0xf99c39), 2.0)       # Pen used when the node is selected.
            self.background = Qt.GlobalColor.white              # Default background color of the node.

    # Initializer:
    def __init__(self, 
                 _name  : str,
                 _spos  : QPointF, 
                 _parent: QGraphicsItem | None = None,
                 **kwargs
                ):
        """
        Instantiate a new _node with the given name, coordinates, and parent.

        :param: _name  (str)            : The name of the node (displayed at the top in an editable text-box).
        :param: _spos  (QPointF)        : The position of the node (in scene-coordinates).
        :param: _parent(QGraphicsItem)  : The node's parent item (usually `None`).
        """

        # Validate argument(s):
        if not isinstance(_name, str):      raise TypeError("Expected argument of type `str`")
        if not isinstance(_spos, QPointF):  raise TypeError("Expected argument of type `QPoint`")

        # Initialize super-class:
        super().__init__(_parent)

        # Initialize style and attrib:
        self._nuid = str()              # The _node's unique ID
        self._spos = _spos              # Used to track and emit signal if the _node has been moved
        self._styl = self.Style()       # Instantiate the _node's style
        self._attr = self.Attr()        # Instantiate the _node's attribute
        self._data = dict({
            EntityClass.INP:    dict(), # Dictionary for input variable(s)
            EntityClass.OUT:    dict(), # Dictionary for output variable(s)
            EntityClass.PAR:    dict(), # Dictionary for parameters
            EntityClass.EQN:    list()  # List of equations
        })

        # Customize behaviour:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Label to display the _node's unique identifier:
        self._label = Label(self, self._nuid, 
                            width=60,
                            color=QColor(0xadadad), 
                            align=Qt.AlignmentFlag.AlignLeft,
                            editable=False)

        # Label to display the _node's name:
        self._title = Label(self, _name,
                            width=120,
                            align=Qt.AlignmentFlag.AlignCenter,
                            editable=True)

        # Position labels:
        self._label.setPos(-98, -72)
        self._title.setPos(-60, -72)

        # Header-buttons:
        _expand = Button("rss/icons/expand.svg", self)
        _shrink = Button("rss/icons/shrink.svg", self)
        _remove = Button("rss/icons/delete.svg", self)

        _expand.moveBy(70, -59)
        _shrink.moveBy(70, -65)
        _remove.moveBy(86, -62)

        _expand.sig_button_clicked.connect(lambda: self.resize( self._attr.delta))
        _shrink.sig_button_clicked.connect(lambda: self.resize(-self._attr.delta))
        _remove.sig_button_clicked.connect(self.sig_item_removed.emit)

        # Instantiate separator:
        _hline = QGraphicsLineItem(QLineF(-96, 0, 96, 0), self)
        _hline.moveBy(0, -48)

        self._divider = QGraphicsLineItem(QLineF(0, -40, 0, 68), self)
        self._divider.setPen(QPen(Qt.GlobalColor.gray, 0.5))

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

        # Process keyword-arguments:
        if "uid" in kwargs:    self.uid = kwargs.get("uid")

    def __getitem__(self, _eclass: EntityClass):
        """
        Returns a dictionary or list depending on the entity sought:

        Args:
            _eclass (EntityClass): Class of the entity (INP, OUT, PAR, or EQN)

        Returns:
            dict | list: Dictionary or list
        """

        if _eclass == EntityClass.VAR:  return self._data[EntityClass.INP] | self._data[EntityClass.OUT]
        else:                           return self._data[_eclass]

    def __setitem__(self,
                    _tuple: tuple,
                    _value: EntityState | str | list
                    ):
        """
        Sets the state of an entity belonging to the _node.

        Args:
            _tuple (tuple): A tuple containing the entity class and the entity.
            _value (EntityState | str | list): The state to set for the entity.
        """

        # Validate argument(s):
        if not isinstance(_tuple, tuple): raise TypeError("Expected argument of type `tuple`")

        # Resolve tuple:
        _eclass, _entity = _tuple

        # Assign data:
        if  _eclass in [EntityClass.INP, EntityClass.OUT, EntityClass.PAR]:
            self._data[_eclass][_entity] = _value

        if  _eclass == EntityClass.EQN:
            self._data[_eclass] = _value

    def _init_menu(self):
        """
        Adds actions to the context menu and connects them to appropriate slots.

        Returns: 
            None
        """

        # Add actions to menu:
        _template = self._menu.addAction("Save as Template", lambda: print("Save as Template"))

        # Additional actions:
        self._menu.addSeparator()
        _expand = self._menu.addAction(QIcon("rss/icons/expand.svg"), "Expand", lambda: self.resize( self._attr.delta))
        _shrink = self._menu.addAction(QIcon("rss/icons/shrink.svg"), "Shrink", lambda: self.resize(-self._attr.delta))

        # Additional actions:
        self._menu.addSeparator()
        _close = self._menu.addAction(QIcon("rss/icons/menu-delete.png"), "Delete", self.sig_item_removed.emit)

        # Make icons visible:
        _expand.setIconVisibleInMenu(True)
        _shrink.setIconVisibleInMenu(True)
        _close.setIconVisibleInMenu(True)

    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Implementation of QGraphicsObject.boundingRect() (see Qt documentation).
    # 2. paint                  Implementation of QGraphicsObject.paint() (see Qt documentation).
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self):
        """
        Re-implementation of QGraphicsObject.boundingRect().

        Returns:
            QRectF: The bounding rectangle of the _node.
        """

        # Return bounding-rectangle:
        return self._attr.rect

    def paint(self, _painter, _option, _widget = ...):
        """
        Re-implementation of QGraphicsObject.paint().

        Args:
            _painter (QPainter) : The painter object.
            _option (QStyleOptionGraphicsItem) : The option object.
            _widget (QWidget) : The widget object.
        """

        # Select different pens for selected and unselected states:
        _pen = self._styl.pen_select if self.isSelected() else self._styl.pen_border
                 
        # Draw border:
        _painter.setPen(_pen)
        _painter.setBrush(self._styl.background)
        _painter.drawRoundedRect(self._attr.rect, 12, 6)

    def itemChange(self, change, value):

        # Import canvas module:
        from tabs.schema import SaveState

        # If this node has been added to a canvas:
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged and value:

            # Connect node's signals to the canvas's slots:
            self.sig_item_updated.connect(lambda: value.sig_canvas_state.emit(SaveState.MODIFIED))
            self.sig_item_removed.connect(value.on_item_removed)

            # Connect signal-exec actions:
            self.sig_exec_actions.connect(lambda: value.sig_canvas_state.emit(SaveState.MODIFIED))
            self.sig_exec_actions.connect(value.manager.do)

            # Forward handle's signals:
            self.sig_handle_clicked.connect(value.begin_transient)

            # Adjust scene-position:
            self.setPos(self._spos)

        return value

    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. hoverEnterEvent        Triggered when the mouse enters the _node.
    # 2. hoverLeaveEvent        Triggered when the mouse leaves the _node.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Triggered when the context menu is requested.

        Args:
            event (QContextMenuEvent) : Context-menu event, instantiated by Qt.
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
        Triggered when the mouse enters the _node.

        Args:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.
        """
        super().hoverEnterEvent(event)              # Forward to super-class
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Set arrow-cursor
    
    def hoverLeaveEvent(self, event):
        """
        Triggered when the mouse leaves the _node.

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
        
        # If the _node has been moved, notify canvas:
        if  self.scenePos() != self._spos:
            self.sig_item_updated.emit()

    # User-defined methods ---------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. clone                  Duplicates the _node.
    # 2. resize                 Resizes the _node in discrete steps.
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

        _vars = [
            variable for variable, state in self[EntityClass.VAR].items()
            if state == EntityState.ACTIVE
        ]

        _pars = [
            parameter for parameter, state in self[EntityClass.PAR].items()
            if state == EntityState.ACTIVE
        ]

        _eqns = self._data[EntityClass.EQN].copy()

        # Create a dictionary of symbol-replacements:
        replacements  = dict()

        # Variable symbols (R00, P00, ...) are replaced with connector symbols (X0, X1, ...)
        for var in _vars:
            replacements[var.symbol] = var.connector().symbol if var.connected else None

        # Parameters symbols are prefixed with the _node's UID:
        for par in _pars:
            replacements[par.symbol] = f"{node_prefix}_{par.symbol}"

        # Modify all equations:
        for equation in _eqns:
            tokens = equation.split(' ')
            update = [replacements.get(token, token) for token in tokens]

            if not None in update:
                transformed.append(str(" ").join(update))

        return transformed

    def clone(self, **kwargs):
        """
        Create an identical copy of this _node.

        Returns:
            Node: A new _node with the same properties as the original _node.
        """

        # Instantiate a new _node:
        _node = Node(self._title.toPlainText(),
                     self.scenePos() + QPointF(25, 25),
                     self.parentItem()
                     )

        # Adjust _node-height:
        _diff = self.boundingRect().height() - _node.boundingRect().height()
        _node.resize(_diff)
        _node.setSelected(self.isSelected())

        # Construct lists of active data:
        _var_active = [_variable  for _variable , _state in self[EntityClass.VAR].items() if _state == EntityState.ACTIVE]
        _par_active = [_parameter for _parameter, _state in self[EntityClass.PAR].items() if _state == EntityState.ACTIVE]

        # Copy this _node's variable(s):
        for _entity in _var_active:

            # Instantiate new handle and copy attribute(s):
            _copied = _node.create_handle(_entity.eclass,_entity.pos())
            _entity.clone_into(_copied)

            # Add copied variable to the _node's registry:
            _node[_entity.eclass][_copied] = EntityState.ACTIVE
            Handle.cmap[_entity] = _copied

        # Copy this _node's parameter(s):
        for _entity in _par_active:
            _copied = Entity()              # Instantiate a new entity
            _entity.clone_into(_copied)     # Copy attributes into the new entity

            # Add copied variable to the _node's registry:
            _node[_entity.eclass][_copied] = EntityState.ACTIVE

        # Deselect this _node:
        self.setSelected(False)

        # Process keyword-args:
        if "set_uid" in kwargs: _node.uid = kwargs.get("set_uid")

        # Return reference to the created _node:
        return _node

    def resize(self, delta: int | float):
        """
        Resizes the _node in discrete steps.

        Args:
            delta (int) : Increment or decrement step-size.
        """

        # Set a minimum _node-height:
        if delta < 0 and self._attr.rect.height() < 200: return

        # Resize _node, adjust contents:
        self._attr.rect.adjust(0, 0, 0, delta)
        self._anchor_inp.resize(delta)
        self._anchor_out.resize(delta)

        self._divider.setLine(self._anchor_inp.line)
        self._divider.setX(0)
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

    def create_handle(self,
                      _eclass: EntityClass,
                      _coords: QPointF,
                      _clone : Handle = None
                      ):
        """
        Creates a new handle at the given coordinate, returns reference to the handle.

        Args:
            _eclass (EntityClass): The stream-direction of the new handle (INP or OUT).
            _coords (QPointF)    : The coordinates of the new handle (must be in the _node's coordinate-system).
            _clone (Handle)      : If provided, the created handle will be a clone of this handle

        Returns:
            Handle: Reference to the new handle.
        """

        # Instantiate a new handle:
        _handle = Handle(_eclass,
                         _coords,
                         self.create_huid(_eclass),
                         self
                        )

        # Connect handle's signals to the _node's slots:
        _handle.sig_item_clicked.connect(self.sig_handle_clicked.emit)
        _handle.sig_item_updated.connect(self.sig_handle_updated.emit)
        _handle.sig_item_cleared.connect(self.on_handle_cleared)
        _handle.sig_item_removed.connect(self.on_handle_removed)

        # Add handle to the _node's database:
        self[_eclass][_handle] = EntityState.ACTIVE

        # Return reference to handle:
        return _handle 

    def create_huid(self, _eclass: EntityClass):
        """
        Creates a unique identifier for each handle.

        Returns:
            str: The unique identifier for the handle.
        """

        # Validate argument(s):
        if _eclass not in [EntityClass.INP, EntityClass.OUT]: raise ValueError("Expected argument: `EntityClass.INP` or `EntityClass.OUT`")

        # Create a unique handle-identifier:
        prefix = "P" if _eclass == EntityClass.OUT else "R"
        id_set = {
            int(handle.symbol[1:])         # Get the _node's currently used symbols
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
    def on_anchor_clicked(self, _coords: QPointF):
        """
        Triggered when an anchor is clicked.

        :param: _coords (QPointF): The coordinates where the anchor was clicked, in scene-coordinates.
        """

        # Validate argument(s):
        _anchor = self.sender()
        if not isinstance(_coords, QPointF): raise TypeError("Expected argument of type `QPointF`")
        if not isinstance(_anchor, Anchor) : raise TypeError("Expected signal-emitter of type `Anchor`")

        # Create a new handle at the anchor's position:
        _eclass = _anchor.stream()                          # Get anchor's stream (EntityClass.INP or EntityClass.OUT)
        _coords = self.mapFromItem(_anchor, _coords)        # Map coordinate to _node's coordinate-system
        _handle = self.create_handle(_eclass, _coords)
        _handle.sig_item_clicked.emit(_handle)              # Emit signal to begin transient-connection.

        # Enter handle into the _node's database:
        self[_eclass, _handle] = EntityState.ACTIVE         # Set state `EntityState.ACTIVE`

        # Notify application of state-change:
        self.sig_exec_actions.emit(CreateHandleAction(self, _handle))
        self.sig_item_updated.emit()
    
    # Triggered when a handle is removed:
    def on_handle_removed(self, _handle: Handle):
        # Create an undoable remove-action and notify actions-manager:
        self.sig_exec_actions.emit(RemoveHandleAction(self, _handle))

    # Triggered when a handle is cleared:
    def on_handle_cleared(self, handle: Handle):
        
        # Create an undoable disconnect-action:
        _action = DisconnectHandleAction(self.scene(), handle.connector())

        # Emit signal to disconnect handle:
        self.sig_exec_actions.emit(_action)

    # Properties -------------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. uid                   The _node's unique identifier.
    # 2. name                  The _node's name.
    # ------------------------------------------------------------------------------------------------------------------
    
    @property
    def uid(self):  return self._nuid
    
    @property
    def title(self): return self._title.toPlainText()

    @uid.setter
    def uid(self, value: str):
        self._nuid = value
        self._label.setPlainText(value)

    @title.setter
    def title(self, value: str):
        self._title.setPlainText(value)
