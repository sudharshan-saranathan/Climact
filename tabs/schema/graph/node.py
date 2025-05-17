from PyQt6.QtGui import (
    QPen, 
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

    # Signals:
    sig_item_updated = pyqtSignal()
    sig_item_removed = pyqtSignal()
    sig_exec_actions = pyqtSignal(AbstractAction)

    sig_handle_clicked = pyqtSignal(Handle)
    sig_handle_updated = pyqtSignal(Handle)
    sig_handle_removed = pyqtSignal(Handle)

    # Global lists:
    class Register:
        def __init__(self):
            self.data = dict()
            self.eqns = set()

    # Default Attrib:
    class Attr:
        def __init__(self):
            self.rect  = QRectF(-100, -75, 200, 150)
            self.auto  = dict()
            self.steps = 0
            self.delta = 50

    # Style:
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.black, 2.0)
            self.pen_select = QPen(QColor(0xf99c39), 2.0)
            self.background = Qt.GlobalColor.white

    # Initializer:
    def __init__(self, 
                 _name  : str,
                 _spos  : QPointF, 
                 _parent: QGraphicsItem | None = None):

        """
        Instantiates a new node with the given name, coordinates, and parent.

        Parameters:
            _name  (str)       : The name of the node.
            _spos  (QPointF)   : The position of the node (in scene-coordinates).
            _parent(QGraphicsItem): The parent item of the node.
        """

        # Validate argument(s):
        if not isinstance(_name, str)       : raise TypeError("Expected argument of type `str`")
        if not isinstance(_spos, QPointF)   : raise TypeError("Expected argument of type `QPoint`")

        # Initialize base-class:
        super().__init__(_parent)

        # Initialize style and attrib:
        self._nuid = str()
        self._spos = _spos
        self._styl = self.Style()
        self._attr = self.Attr()
        self._data = dict({
            EntityClass.INP:    dict(), # Dictionary for input variable(s)
            EntityClass.OUT:    dict(), # Dictionary for output variable(s)
            EntityClass.PAR:    dict(), # Dictionary for parameters
            EntityClass.EQN:    list()  # List of equations
        })

        # Adjust behaviour:
        self.setPos(_spos)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Label to display the node's unique identifier:
        self._label = Label(self, self._nuid, 
                            width=60,
                            color=QColor(0xadadad), 
                            align=Qt.AlignmentFlag.AlignLeft,
                            editable=False)

        # Label to display the node's name:
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

    def __getitem__(self, _eclass: EntityClass):
        """
        Returns a dictionary or list depending on the entity sought:

        Parameters:
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

        Parameters: None
        Returns: None
        """

        # Add actions to menu:
        _templated = self._menu.addAction("Save as Template")

        # Additional actions:
        self._menu.addSeparator()
        _expand = self._menu.addAction("Expand")
        _shrink = self._menu.addAction("Shrink")

        # Additional actions:
        self._menu.addSeparator()
        _n_copy = self._menu.addAction("Duplicate")
        _remove = self._menu.addAction("Delete")

        # Connect actions to slots:
        _expand.triggered.connect(lambda: self.resize( self._attr.delta))
        _shrink.triggered.connect(lambda: self.resize(-self._attr.delta))
        _remove.triggered.connect(self.sig_item_removed.emit)

        # Connect actions to slots:
        _n_copy.triggered.connect(lambda: self.duplicate(self.scene()))

    # Re-implemented methods -------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. boundingRect           Implementation of QGraphicsObject.boundingRect() (see Qt documentation).
    # 2. paint                  Implementation of QGraphicsObject.paint() (see Qt documentation).
    # ------------------------------------------------------------------------------------------------------------------

    def boundingRect(self):
        """
        Returns the bounding rectangle of the node. This method must be implemented by subclasses of QGraphicsObject.

        Returns:
            QRectF: The bounding rectangle of the node.
        """

        # Return bounding-rectangle:
        return self._attr.rect

    def paint(self, painter, option, widget = ...):
        """
        Paints the node on the canvas.

        Parameters:
            painter (QPainter) : The painter object.
            option (QStyleOptionGraphicsItem) : The option object.
            widget (QWidget) : The widget object.
        """

        # Select different pens for selected and unselected states:
        _pen = self._styl.pen_select if self.isSelected() else self._styl.pen_border
                 
        # Draw border:
        painter.setPen(_pen)
        painter.setBrush(self._styl.background)
        painter.drawRoundedRect(self._attr.rect, 12, 6)

    # Event-handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. hoverEnterEvent        Triggered when the mouse enters the node.
    # 2. hoverLeaveEvent        Triggered when the mouse leaves the node.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Triggered when the context menu is requested.

        Parameters:
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
        Triggered when the mouse enters the node.

        Parameters:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.
        """
        super().hoverEnterEvent(event)              # Forward to super-class
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Set arrow-cursor
    
    def hoverLeaveEvent(self, event):
        """
        Triggered when the mouse leaves the node.

        Parameters:
            event (QHoverEvent) : Hover event, triggered and managed by Qt.
        """
        super().hoverLeaveEvent(event)              # Forward to super-class
        self.unsetCursor()                          # Unset cursor

    def mouseReleaseEvent(self, event):
        """
        Triggered when the mouse is released.

        Parameters:
            event (QMouseEvent) : Mouse event, instantiated by Qt.
        """

        # Forward event to super-class:
        super().mouseReleaseEvent(event)
        
        # If the node has been moved, notify canvas:
        if  self.scenePos() != self._spos:
            self.sig_item_updated.emit()

    # User-defined methods ---------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. duplicate              Duplicates the node.
    # 2. resize                 Resizes the node in discrete steps.
    # 3. create_handle          Creates a new handle.
    # 4. create_huid            Creates a unique identifier for each handle.
    # 5. on_anchor_clicked      Triggered when an anchor is clicked.
    # 6. on_handle_clicked      Triggered when a handle is clicked.
    # 7. on_handle_updated      Triggered when a handle is updated.
    # 8. on_handle_removed      Triggered when a handle is removed.
    # ------------------------------------------------------------------------------------------------------------------

    # Return transformed equations:
    def substituted(self)   -> list[str]:

        transformed = list()
        node_prefix = self.uid

        vars = [
            variable for variable, state in self[EntityClass.VAR].items()
            if state == EntityState.ACTIVE
        ]

        pars = [
            parameter for parameter, state in self[EntityClass.PAR].items()
            if state == EntityState.ACTIVE
        ]

        eqns = self._data[EntityClass.EQN].copy()

        # Create a dictionary of symbol-replacements:
        replacements  = dict()

        # Variable symbols (R00, P00, ...) are replaced with connector symbols (X0, X1, ...)
        for var in vars:
            replacements[var.symbol] = var.connector().symbol if var.connected else None

        # Parameters symbols are prefixed with the node's UID:
        for par in pars:
            replacements[par.symbol] = f"{node_prefix}_{par.symbol}"

        # Modify all equations:
        for equation in eqns:
            tokens = equation.split(' ')
            update = [replacements.get(token, token) for token in tokens]

            if not None in update:
                transformed.append(str(" ").join(update))

        return transformed

    def duplicate(self, _canvas = None):
        """
        Duplicates the node.

        Returns:
            Node: A new node with the same properties as the original node.
        """

        # Duplicate node:
        _npos = self.scenePos() + QPointF(25, 25)           # Shift node slightly to the right.
        _node = Node(self.title, _npos, self.parentItem())  # Create new node.

        _diff = self._attr.rect.height() - _node._attr.rect.height()
        _node.resize(_diff)
        _node.setSelected(self.isSelected())                # Copy selection-state.

        # Copy the contents of the current node:
        for _entity, _state in (self[EntityClass.VAR] | self[EntityClass.PAR]).items():

            # Ignore hidden handles:
            if _state == EntityState.HIDDEN: continue

            # Create a copied entity (parameter or handle):
            copied = _node.create_handle(
                _entity.pos(), 
                _entity.eclass
            ) \
                if _entity.eclass in [EntityClass.INP, EntityClass.OUT] else Entity()
            
            # Add entity and its copy to the handle-map:
            if _entity.eclass in [EntityClass.INP, EntityClass.OUT]:    Handle.cmap[_entity] = copied

            # Rename copied handle:
            copied.rename(_entity.label)
        
            # Copy entity's attributes:
            copied.info    = _entity.info
            copied.units   = _entity.units
            copied.strid   = _entity.strid
            copied.color   = _entity.color
            copied.value   = _entity.value
            copied.sigma   = _entity.sigma
            copied.minimum = _entity.minimum
            copied.maximum = _entity.maximum

            # Add copied variable to the node's registry:
            _node[_entity.eclass][copied] = EntityState.ACTIVE
        
        # Copy equations:
        # [_node.equations.add(equation) for equation in self.equations]

        # Import Canvas:
        from tabs.schema.canvas import Canvas
        if isinstance(_canvas, Canvas):
            _canvas.paste_item(_node)

        # Deselect this node:
        self.setSelected(False)

        # Return reference to the created node:
        return _node

    def resize(self, delta: int | float):
        """
        Resizes the node in discrete steps.

        Parameters:
            delta (int) : Increment or decrement step-size.
        """

        # Set a minimum node-height:
        if delta < 0 and self._attr.rect.height() < 200: return

        # Resize node, adjust contents:
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
                      _coords: QPointF, 
                      _eclass: EntityClass
                      ):
        """
        Creates a new handle at the given coordinate, returns reference to the handle.

        Parameters:
            _coords (QPointF) : The coordinates of the new handle (must be in the node's coordinate-system).
            _eclass (EntityClass) : The stream-direction of the new handle (INP or OUT).

        Returns:
            Handle: Reference to the new handle.
        """

        # Create handle, connect signals to appropriate slots:
        _handle = Handle(self.create_huid(_eclass), _coords, _eclass, self)
        _handle.sig_item_clicked.connect(self.sig_handle_clicked.emit)
        _handle.sig_item_updated.connect(self.sig_handle_updated.emit)
        _handle.sig_item_cleared.connect(self.on_handle_cleared)
        _handle.sig_item_removed.connect(self.on_handle_removed)

        # Add handle to the node's database:
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
    def on_anchor_clicked(self, _coords: QPointF):
        """
        Triggered when an anchor is clicked.

        Parameters:
            _coords (QPointF): The click-position in anchor's coordinate-system.
        """

        # Validate argument(s):
        _anchor = self.sender()
        if not isinstance(_coords, QPointF) : raise TypeError("Expected argument of type `QPointF`")
        if not isinstance(_anchor, Anchor)  : raise TypeError("Expected signal-emitter of type `Anchor`")

        # Create handle at anchor's position:
        _eclass = _anchor.stream()                          # Get anchor's stream (EntityClass.INP or EntityClass.OUT)
        _coords = self.mapFromItem(_anchor, _coords)        # Map coordinate to node's coordinate-system
        _handle = self.create_handle(_coords,      # Create handle at the requested position
                                     _eclass
                                     )
        _handle.sig_item_clicked.emit(_handle)              # Emit signal to begin transient-connection.

        # Enter handle into the node's database:
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
        self._label.setPlainText(value)

    @title.setter
    def title(self, value: str):
        self._title.setPlainText(value)
