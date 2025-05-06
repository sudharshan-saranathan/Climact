from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPoint, QLineF, pyqtSlot, QPointF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QMenu, QGraphicsLineItem

from core.button import Button
from core.label import Label
from core.resource import Resource
from core.util import random_id

from tabs.schema.action       import *
from tabs.schema.graph.anchor import Anchor, StreamType
from tabs.schema.graph.handle import Handle

class Node(QGraphicsObject):

    # Signals:
    sig_item_updated = pyqtSignal()
    sig_item_removed = pyqtSignal()
    sig_handle_clicked = pyqtSignal(Handle)
    sig_handle_updated = pyqtSignal(Handle)
    sig_handle_removed = pyqtSignal(Handle)
    sig_execute_action = pyqtSignal(AbstractAction)

    # Global lists:
    class Entity:
        def __init__(self):
            self.inp = dict()
            self.out = dict()
            self.par = dict()
            self.eqn = set()

    # Lists:
    class Symbol:
        def __init__(self):
            self.inp = set()
            self.out = set()
            self.par = set()

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
    def __init__(self, coordinate: QPoint, name: str = "Node", parent: QGraphicsItem | None = None):

        # Initialize base-class:
        super().__init__(parent)

        # Initialize keywords:
        self.setPos(coordinate.toPointF())
        self.setObjectName(name)

        # Initialize style and attrib:
        self._styl = self.Style()
        self._attr = self.Attr()
        self._data = self.Entity()
        self._tags = self.Symbol()

        # Assign node ID:
        self._nuid = random_id(length=4, prefix='N')

        # Adjust behaviour:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        # Node-items:
        self._label = Label(self,
                            edit=False,
                            font=QFont("Fira Sans", 10),
                            width=60,
                            label=self._nuid,
                            color=QColor(0xadadad),
                            align=Qt.AlignmentFlag.AlignCenter)

        self._title = Label(self,
                            edit=True,
                            font=QFont("Fira Sans", 13),
                            width=120,
                            label=name,
                            color=QColor(0x0),
                            align=Qt.AlignmentFlag.AlignCenter)

        self._label.setPos(-108, -72)
        self._title.setPos( -60, -74)

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

        # Separator:
        _hline = QGraphicsLineItem(QLineF(-96, 0, 96, 0), self)
        _hline.moveBy(0, -48)

        self._divider = QGraphicsLineItem(QLineF(0, -40, 0, 68), self)
        self._divider.setPen(QPen(Qt.GlobalColor.gray, 0.5))

        # Anchors:
        self._anchor_inp = Anchor(StreamType.INP, self)
        self._anchor_out = Anchor(StreamType.OUT, self)

        self._anchor_inp.setPos(-95, 0)
        self._anchor_out.setPos( 95, 0)

        self._anchor_inp.sig_item_clicked.connect(self.on_anchor_clicked)
        self._anchor_out.sig_item_clicked.connect(self.on_anchor_clicked)

        # Initialize menu:
        self._menu = None
        self._init_menu()

    def _init_menu(self):
        self._menu = QMenu()

    def __hash__(self):
        return hash(self._nuid)

    def __eq__(self, other):
        return isinstance(other, Node) and self._nuid == other._nuid

    # Get stream-lists:
    def __getitem__(self, stream: StreamType):

        if stream == StreamType.INP:
            return self._data.inp

        elif stream == StreamType.OUT:
            return self._data.out

        elif stream == StreamType.PAR:
            return self._data.par

        else:
            logging.warning(f"Unrecognized stream type")
            return None

    # Set parameter list:
    def __setitem__(self, key: StreamType, value):

        if  not isinstance(value, list) or \
            not isinstance(key, StreamType):
            return None

        if key == StreamType.PAR:
            self._data.par = value.copy()

    @property
    # Gets the node's UID:
    def uid(self):  return self._nuid

    @uid.setter
    def uid(self, value):
        self._nuid = value if isinstance(value, str) else self.uid
        self._label.setPlainText(self._nuid)

    @property
    # Gets the node's name:
    def name(self):
        return self._title.toPlainText()

    @property
    # Gets the border-pen:
    def border(self):   return self._styl.pen_border

    @border.setter
    # Sets the border-pen:
    def border(self, _value):   self._styl.pen_border = _value if isinstance(_value, QPen) else self.border

    def symbol(self, stream: StreamType):

        if stream == StreamType.INP:
            return self._tags.inp

        if stream == StreamType.OUT:
            return self._tags.out

        if stream == StreamType.PAR:
            return self._tags.par

        logging.warning("Node.symbol(): Unrecognized stream type")
        return None

    def print(self):

        total = self[StreamType.INP] | self[StreamType.OUT]
        for handle in total:
            print(handle, total[handle])

    # Paint-event handler:
    def paint(self, painter, option, widget = ...):
        painter.setPen  (self._styl.pen_select if self.isSelected() else self._styl.pen_border)
        painter.setBrush(self._styl.background)
        painter.drawRoundedRect(self._attr.rect, 12, 6)

    # ItemChange handler:
    def itemChange(self, change, value):

        # Import Canvas:
        from tabs.schema.canvas import Canvas

        # Handle scene-changes:
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:

            if isinstance(value, Canvas):
                self.sig_item_removed.connect(value.on_item_removed, Qt.ConnectionType.UniqueConnection)

            elif value is None:
                self.sig_item_removed.disconnect()

        return value

    # Returns the bounding rectangle of this item:
    def boundingRect(self):
        return self._attr.rect

    # Hover-event handler:
    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverEnterEvent(event)

    # Hover-event handler:
    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    # Double-click handler:
    def mouseDoubleClickEvent(self, event):

        for handle in self.variables:
            print(handle.symbol, handle.value)

        super().mouseDoubleClickEvent(event)

    # Creates a handle at the specified coordinate:
    def create_handle(self,
                      cpos  : QPointF,
                      symbol: str,
                      stream: StreamType
                      ):

        # Create handle and add to operations-stack:
        handle = Handle(cpos, symbol, stream, self)
        handle.sig_item_clicked.connect(self.sig_handle_clicked.emit)
        handle.sig_item_updated.connect(self.sig_handle_updated.emit)
        handle.sig_item_removed.connect(self.remove_handle)

        # Return reference:
        return handle

    # Removes handle(s):
    @pyqtSlot()
    @pyqtSlot(Handle)
    def remove_handle(self, handle: Handle | None = None):

        handle = self.sender()
        if not isinstance(handle, Handle):
            return

        action = RemoveHandleAction(self, handle)
        self.sig_execute_action.emit(action)

    # Returns a unique symbol:
    def unique_symbol(self, stream: StreamType):

        if stream == StreamType.PAR:
            return None

        _prefix  = 'R'            if stream == StreamType.INP else 'P'
        _varlist = self._data.inp if stream == StreamType.INP else self._data.out   # Variable list

        indices = set()
        for variable in _varlist:
            if variable.isEnabled():
                indices.add(int(variable.symbol.split(_prefix)[1]))

        if not indices:
            return _prefix + str("00")

        sequence = set(range(0, max(indices) + 2))
        reusable = sequence - indices

        return _prefix + str(min(reusable)).zfill(2)

    @pyqtSlot(QPointF)
    # Creates a handle where the anchor was clicked:
    def on_anchor_clicked(self, coordinate: QPointF):

        anchor = self.sender()
        if not isinstance(anchor, Anchor):
            return

        # Get handle-attributes:
        stream = anchor.stream()
        coords = anchor.mapToParent(coordinate)

        handle = self.create_handle(coords, self.unique_symbol(stream), stream)
        handle.sig_item_clicked.emit(handle)

        # Notify action-manager:
        action = CreateHandleAction(self, handle)
        self.sig_execute_action.emit(action)

    @pyqtSlot(int)
    # Resizes the node in discrete steps:
    def resize(self, delta: int):

        if not isinstance(delta, int):
            return

        if delta < 0 and self._attr.rect.height() < 200:
            return

        self._anchor_inp.resize(delta)
        self._anchor_out.resize(delta)

        self._divider.setLine(self._anchor_inp.line)
        self._divider.setX(0)
        self.update()

        shifted_bottom = self._attr.rect.bottom() + delta
        self._attr.rect.setBottom(shifted_bottom)
        self._attr.steps += int(delta / self._attr.delta)

    # Creates a duplicate of the node:
    def duplicate(self, canvas):

        cpos = self.scenePos().toPoint() + QPoint(25, 25)
        name = self._title.toPlainText()

        node = Node(cpos, name)
        node.setSelected(True)

        # Create batch-actions with node-creation as the first task:
        batch = BatchActions([])
        batch.add_to_batch(CreateNodeAction(canvas, node))

        # Resize the copied node:
        delta = self._attr.rect.height() - 50
        node.resize(delta)

        # Copy input/output streams:
        for handle in self.variables:

            # Create an identical handle with the same coordinate, symbol, and `StreamType`:
            handle_copy = node.create_handle(handle.pos(), handle.symbol, handle.stream)
            Handle.cmap[handle] = handle_copy

            # Copy properties:
            handle_copy.label   = handle.label
            handle_copy.units   = handle.units
            handle_copy.value   = handle.value
            handle_copy.sigma   = handle.sigma
            handle_copy.cname   = handle.cname
            handle_copy.minimum = handle.minimum
            handle_copy.maximum = handle.maximum

            # Add handle-creation to batch:
            batch.add_to_batch(CreateHandleAction(node, handle_copy))

        # Copy parameter(s):
        for parameter in self.parameters.keys():

            resource = Resource()
            resource.symbol  = parameter.symbol
            resource.label   = parameter.label
            resource.units   = parameter.units
            resource.value   = parameter.value
            resource.sigma   = parameter.sigma
            resource.cname   = parameter.cname
            resource.minimum = parameter.minimum
            resource.maximum = parameter.maximum
            node._data.par[resource] = True

        # Copy equation(s):
        for equation in self.equations:
            node.equations.add(equation)

        # Return node and batch-actions:
        return node, batch

    @property
    # Gets the node's handles (disabled handles are ignored):
    def variables(self)   -> set:

        hset = set()
        for handle in self[StreamType.INP] | self[StreamType.OUT]:
            if handle.isVisible():
                hset.add(handle)

        return hset

    @property
    # Gets the node's parameters:
    def parameters(self)    -> dict:    return self._data.par

    @parameters.setter
    # Sets the node's parameters:
    def parameters(self, dictionary):
        if isinstance(dictionary, dict):
            self._data.par = dictionary

    @property
    # Returns the node's equations:
    def equations(self) -> set:    return self._data.eqn

    @equations.setter
    def equations(self, value):
        self._data.eqn = value if isinstance(value, set) else self.equations

    # Return transformed equations:
    def substituted(self)   -> list[str]:

        transformed = list()
        node_prefix = self.uid
        equations   = self.equations.copy()

        # Create a dictionary of symbol-replacements:
        replacements  = dict()

        # Variable symbols (R00, P00, ...) are replaced with connector symbols (X0, X1, ...)
        for var in self.variables:
            replacements[var.symbol] = var.connector().symbol if var.connected else None

        # Parameters symbols are prefixed with the node's UID:
        for par in self.parameters:
            replacements[par.symbol] = f"{node_prefix}_{par.symbol}"

        # Modify all equations:
        for equation in equations:
            tokens = equation.split(' ')
            update = [replacements.get(token, token) for token in tokens]

            if not None in update:
                transformed.append(str(" ").join(update))

        return transformed

    # Return defined symbols as a set:
    def symbols(self) -> set:

        sym_list = set()
        for variable in self.variables:     sym_list.add(variable.symbol)
        for param in self[StreamType.PAR]:  sym_list.add(param.symbol)

        return sym_list