import json
from pathlib import Path

from widgets import schema

from custom.button          import *
from custom.input import Input
from widgets.schema.graph.handle import *

class Node(QGraphicsObject):

    # User-defined signals:
    sig_item_updated   = pyqtSignal()       # Emitted to notify the database (triggers the canvas' sig_tree_refresh())
    sig_item_deleted   = pyqtSignal()       # Emitted to notify the database (triggers the canvas' sig_tree_refresh())

    sig_handle_clicked = pyqtSignal(Handle)
    sig_handle_created = pyqtSignal(Handle)
    sig_handle_updated = pyqtSignal(Handle)
    sig_handle_deleted = pyqtSignal(Handle)

    # Node attrib:
    class Attr:
        type = QGraphicsItem.UserType + 1
        def __init__(self):
            self.step = 0
            self.delt = 50
            self.rect = QRectF(-150, -100, 300, 200)

    class Sector:
        def __init__(self):
            self.group = "None"

    # Metadata:
    class Meta:
        def __init__(self):
            self.inp = list()
            self.out = list()
            self.par = list()
            self.eqn = list()

            self.inp_reusable = list()
            self.out_reusable = list()
            self.item_group   = QGraphicsItemGroup(None)

    # Node style:
    class Style:
        pen_default = QPen(QColor(0x000000), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        pen_hovered = QPen(QColor(0x0a0a0a), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        pen_focused = QPen(QColor(0xffa51f), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        pen_current = pen_default
        background  = QBrush(Qt.GlobalColor.white)

    # Initialization:
    def __init__(self, name: str = "Node", parent: QGraphicsItem = None):
        super().__init__(parent)    # Initialize base-class

        # Attrib:
        self._attr = self.Attr()
        self._meta = self.Meta()
        self._styl = self.Style()
        self._sect = self.Sector()

        # Initialize menu and setup:
        self.__menu__()

        # Customize header:
        self._nuid = Profile(QSS.random_id(length = 4, prefix="N#"), False, self)
        self._name = Profile(name, True, self)

        self._nuid.setTextWidth(60)
        self._nuid.setDefaultTextColor(Qt.GlobalColor.lightGray)
        self._nuid.setPos(-144, -97.5)

        self._name.setTextWidth(140)
        self._name.sig_text_changed.connect(self.sig_item_updated.emit)
        self._name.set_alignment(Qt.AlignmentFlag.AlignCenter)
        self._name.set_upper_case_only(True)
        self._name.setPos( -74, -97.5)

        # Add icon-buttons to the header:
        _expand = Button("rss/icons/expand.svg", self)
        _shrink = Button("rss/icons/shrink.svg", self)
        _delete = Button("rss/icons/delete.svg", self)

        _expand.moveBy(112, -81)
        _shrink.moveBy(112, -89)
        _delete.moveBy(134, -85)

        # Connect buttons to slots:
        _delete.sig_button_clicked.connect(self.delete)
        _expand.sig_button_clicked.connect(lambda: self.adjust(-self._attr.delt))
        _shrink.sig_button_clicked.connect(lambda: self.adjust( self._attr.delt))

        # Add separator:
        _separator = QGraphicsLineItem(QLineF(-144, 0, 144, 0), self)
        _separator.moveBy(0, -70)

        # Initialize anchors:
        self._anchor_inp = Anchor(Stream.INP, self)
        self._anchor_out = Anchor(Stream.OUT, self)

        self._anchor_inp.setPos(-144, 0)
        self._anchor_out.setPos( 144, 0)

        self._anchor_inp.sig_item_clicked.connect(self.on_anchor_clicked)
        self._anchor_out.sig_item_clicked.connect(self.on_anchor_clicked)

        # Behaviour:
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable , True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable   , True)

    # Context-menu initializer:
    def __menu__(self):

        self._menu = QMenu()
        self._template = self._menu.addAction("Create Template")
        self._delete   = self._menu.addAction("Delete")

        # Behaviour:
        self._menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._template.triggered.connect(self.as_component)
        self._delete.triggered.connect(self.delete)

    # Get list:
    def __getitem__(self, stream):

        if not isinstance(stream, Stream):
            return None

        if stream == Stream.INP:
            return self._meta.inp

        if stream == Stream.OUT:
            return self._meta.out

        if stream == Stream.PAR:
            return self._meta.par

    # Set lists:
    def __setitem__(self, key: Stream, value):

        if not isinstance(value, list):
            return

        if not isinstance(key, Stream):
            return

        if key == Stream.PAR:
            self._meta.par = value.copy()

    # Returns the net-change in the height of the node:
    @property
    def delta(self):
        return self._attr.delt

    @delta.setter
    def delta(self, value: int):
        self._attr.delt = value

    @property
    def equations(self):
        return self._meta.eqn

    @equations.setter
    def equations(self, eqlist):
        if not isinstance(eqlist, list):
            return

        self._meta.eqn = eqlist

    @property
    def group(self):
        return self._sect.group

    @group.setter
    def group(self, group):
        if not isinstance(group, str):
            return

        self._sect.group = group

    # Returns the node's ID:
    def nuid(self):
        return self._nuid.toPlainText()

    # Returns the node's name:
    def name(self):
        return self._name.toPlainText()

    # Returns the user-defined type:
    def type(self):
        return self._attr.type

    # Event-handler for painting:
    def paint(self, painter, option, widget = ...):

        painter.setPen(self._styl.pen_focused if self.isSelected() else self._styl.pen_current)
        painter.setBrush(self._styl.background)
        painter.drawRoundedRect(self._attr.rect, 12, 6)

    # Node cleanup:
    def delete(self):

        # Iterate over input/output streams and delete them:
        while self._meta.inp:
            handle = self._meta.inp.pop()
            handle.delete()

        while self._meta.out:
            handle = self._meta.out.pop()
            handle.delete()

        self.sig_item_deleted.emit()

    # Item changes:
    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:

            # When the node has been added to a scene:
            if isinstance(value, schema.Canvas):

                # self.sig_item_updated.connect(value.sig_tree_refresh.emit)
                self.sig_item_deleted.connect(value.on_item_deleted)

                # Connect signals to the scene's event-handlers:
                self.sig_handle_clicked.connect(value.start_connection)

        return value

    # Returns bounding-rectangle:
    def boundingRect(self):
        return self._attr.rect

    def mousePressEvent(self, event):

        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.select_connections(True)

        # super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):

        nvar = len(self[Stream.INP] + self[Stream.OUT])
        npar = len(self[Stream.PAR])
        neqn = len(self.equations)

        print(f"Node {self.nuid()} has {nvar} handles, {npar} parameters, and {neqn} equations")

    def mouseReleaseEvent(self, event):

        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.select_connections(False)

        self.setSelected(False)
        super().mouseReleaseEvent(event)

    # Event-handler for hover-enter:
    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)

        self._styl.pen_current = self._styl.pen_hovered
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Change cursor to arrow-cursor

    # Event-handler for hover-leave:
    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)

        self._styl.pen_current = self._styl.pen_default
        self.unsetCursor()              # Revert to default cursor

    # Event-handler for context-menus:
    def contextMenuEvent(self, event):

        # Prioritize handling by child-items:
        super().contextMenuEvent(event)
        if event.isAccepted():
            return

        self.setSelected(True)
        self._menu.exec(event.screenPos())  # Open menu
        event.accept()

    @pyqtSlot(QPointF, Stream, bool)
    def create_handle(self, coordinate: QPointF, name: str, stream: Stream, initiate_transient: bool):

        # Create handle and position it:
        handle = Handle(name, stream, self)
        handle.setPos(coordinate)
        handle.snap = coordinate.x()

        # Connect the handle's signals to corresponding slots:
        handle.sig_item_clicked.connect(self.on_handle_clicked)
        handle.sig_item_updated.connect(self.on_handle_updated)
        handle.sig_item_deleted.connect(self.on_handle_deleted)

        # Add the handle to the corresponding list:
        handle_list = self[stream]
        handle_list.append(handle)

        # Emit signal:
        self.sig_item_updated.emit()
        return handle

    @pyqtSlot(QPointF, bool)
    def on_anchor_clicked(self, coordinate: QPointF, initiate_transient: bool):

        anchor = self.sender()
        if not isinstance(anchor, Anchor):
            raise RuntimeError("Expected an anchor custom")

        if anchor.parentItem() is not self:
            raise RuntimeError("Unknown signal emitter")

        stream = anchor.stream()
        coords = anchor.mapToParent(coordinate)
        handle = self.create_handle(coords, self.construct_symbol(stream), stream, True)

        if initiate_transient:
            handle.sig_item_clicked.emit()

    @pyqtSlot()
    def on_handle_clicked(self):

        handle = self.sender()
        self.sig_handle_clicked.emit(handle)

    @pyqtSlot()
    def on_handle_updated(self):

        handle = self.sender()
        self.sig_item_updated.emit()

    @pyqtSlot()
    def on_handle_deleted(self):

        handle = self.sender()
        if not isinstance(handle, Handle):
            return

        if handle.stream() == Stream.PAR:
            print(f"ERROR: Expected an input/output handle, argument is a parameter")
            return

        if handle.stream() == Stream.INP:
            self._meta.inp_reusable.append(int(handle.symbol.split("R")[1]))
            self._meta.inp.remove(handle)

        elif handle.stream() == Stream.OUT:
            self._meta.out_reusable.append(int(handle.symbol.split("P")[1]))
            self._meta.out.remove(handle)

        self._meta.inp_reusable.sort(reverse=True)
        self._meta.out_reusable.sort(reverse=True)
        self.sig_item_updated.emit()

    @pyqtSlot()
    def duplicate(self):

        cpos = self.scenePos() + QPointF(25, 25)
        name = self.name() + "-copy"
        node = Node(name)
        node.setPos(cpos)

        # Resize the copied node:
        delta = self._attr.rect.height() - 200
        node.adjust(delta)

        # Create handles:
        for handle in (self._meta.inp + self._meta.out):

            copy = node.create_handle(handle.pos(), node.construct_symbol(handle.stream()), handle.stream(), False)
            copy.category = handle.category
            copy.color    = handle.color
            copy.snap     = handle.snap

            Handle.cmap[handle] = copy

        return node

    def construct_symbol(self, stream: Stream):

        if stream == Stream.PAR:
            return None

        prefix   = "R"                      if stream == Stream.INP else "P"
        h_list   = self._meta.inp           if stream == Stream.INP else self._meta.out
        reusable = self._meta.inp_reusable  if stream == Stream.INP else self._meta.out_reusable

        if len(reusable) and min(reusable) <= len(h_list):
            h_symbol = min(reusable)
            reusable.remove(h_symbol)
            h_symbol = prefix + str(h_symbol).zfill(2)
            return h_symbol

        else:
            h_symbol = len(h_list)
            h_symbol = prefix + str(h_symbol).zfill(2)
            return h_symbol

    @pyqtSlot()
    def adjust(self, delta: float):

        adjusted_height = self._attr.rect.bottom() + delta
        self._attr.rect.setBottom(adjusted_height)

        self._anchor_inp.adjust(delta)
        self._anchor_out.adjust(delta)
        self.update()

        self._attr.step += int(delta / self._attr.delt)

    @pyqtSlot(name="Node.set_rect")
    def set_rect(self, rect: QRectF):
        self._attr.rect = rect
        self.update()

    @pyqtSlot(name="Node.print_info")
    def print_info(self):

        print(f"\nNode {self.nuid()}")
        print(f"Number of handle(s): {len(self._meta.inp)} (Input), {len(self._meta.out)} (Output)")
        for handle in self._meta.inp:
            print(handle.objectName(), handle.label, handle.category)

        for handle in self._meta.out:
            print(handle.objectName(), handle.label, handle.category)

    @pyqtSlot(name="Node.select_connections")
    def select_connections(self, flag: bool):

        for handle in self._meta.inp + self._meta.out:
            if handle.connected:
                handle.conjugate.parentItem().setSelected(flag)

    def as_component(self):

        json_arr = [schema.JsonLib.serialize(self)]
        dialog   = Input(None,
                         prompt="Enter name",
                         option=True,
                         option_first="Components",
                         option_second="Systems")

        template = {"NODES": json_arr, "CONNECTORS": []}
        folder   = dialog.option.lower()

        print(f"Saving to sub-folder: {folder}")
        if dialog.exec():
            path = f"library/{folder}/{dialog.field}.json"
            file = Path(path)
            file.write_text(json.dumps(template, indent=4))






