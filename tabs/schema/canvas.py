import logging
import weakref

from pathlib            import Path
from PyQt6.QtGui         import QColor, QBrush, QTransform
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QRectF, Qt, QPointF, QPoint, QtMsgType
from PyQt6.QtWidgets import QGraphicsScene, QMenu, QGraphicsObject, QFileDialog, QMessageBox, QApplication, \
    QInputDialog, QLineEdit, QLabel, QColorDialog, QGraphicsItemGroup

from core.dialog import Dialog
from core.resource import Category
from core.util import random_id
from tabs.schema.fileio import JsonLib
from tabs.schema.graph.anchor import Anchor
from tabs.schema.graph.handle import Handle
from tabs.schema.graph.node import Node
from dataclasses    import dataclass

from core.stack                  import ActionsManager
from tabs.schema.action          import *
from tabs.schema.graph.connector import Connector, PathGeometry
from tabs.schema.graph.stream import Stream


# Class Canvas: A QGraphicsScene subclass manager for graphical items:
class Canvas(QGraphicsScene):

    # Signals:
    sig_item_added     = pyqtSignal()   # Emitted when an item is added to the canvas
    sig_item_clicked   = pyqtSignal()   # Emitted when a scene-item is clicked
    sig_canvas_cleared = pyqtSignal()   # Emitted when the canvas is cleared

    @dataclass
    class Transient:
        def __init__(self):
            self.active = False
            self.origin = None
            self.target = None
            self.connector = Connector(None)

    @dataclass
    class Background:
        brush = QBrush(QColor(0xefefef))

    @dataclass
    class Global:
        clipboard = list()

    # CANVAS (Initializers) --------------------------------------------------------------------------------------------
    def __init__(self, rect: QRectF, parent: QObject | None):
        """
        Initialize the canvas with a given rectangular boundary and optional parent

        :param: rect: The initial dimensions of the scene
        :param: parent: Optional parent QObject
        """

        # Initialize base-class:
        super().__init__(parent)

        # Stack-manager:
        self.manager = ActionsManager()

        # Item management:
        self.node_total = 0
        self.node_items = dict()
        self.edge_items = dict()
        self.flow_items = dict()

        # Initialize default resource-categories:
        if Category.find_category_by_label("Default", False) is None:
            Category.Set.add(Category("Default", QColor(Qt.GlobalColor.darkGray)))

        if Category.find_category_by_label("Energy", False) is None:
            Category.Set.add(Category("Energy", QColor("#F6AE2D")))

        if Category.find_category_by_label("Power", False) is None:
            Category.Set.add(Category("Power", QColor("#474973")))

        if Category.find_category_by_label("Mass", False) is None:
            Category.Set.add(Category("Mass", QColor("#028CB6")))

        # Default:
        self._rect = rect
        self._cpos = QPoint()

        # Attrib:
        self.setSceneRect(rect)
        self.setBackgroundBrush(self.Background.brush)
        self.setObjectName(random_id(length=4, prefix='C'))

        # Initialize transient:
        self._transient = self.Transient()
        self.addItem(self._transient.connector)

        # Initialize context-menu:
        self._menu = None
        self._init_menu()

    def _init_menu(self):
        """
        Initializes the context menu with node creation, import/export, and group/clear actions.
        """
        # Create menu:
        self._menu = QMenu()

        # Submenu for creating node_items:
        self._subm = self._menu.addMenu("Create Object")
        _node = self._subm.addAction("Node")
        _node.triggered.connect(self.create_node)

        _src  = self._subm.addAction("Flow (In)")
        _src.triggered.connect(self.create_source)

        _sink = self._subm.addAction("Flow (Out)")
        _sink.triggered.connect(self.create_sink)

        # Open and save actions:
        self._menu.addSeparator()
        _import = self._menu.addAction("Import Schema")
        _import.triggered.connect(self.import_json)

        _export = self._menu.addAction("Export Schema")
        _export.triggered.connect(self.export_json)

        # Group actions:
        self._menu.addSeparator()
        _group = self._menu.addAction("Group Items")
        _group.triggered.connect(self.group)

        _clear = self._menu.addAction("Clear Scene")
        _clear.triggered.connect(self.clear)

    # CANVAS (Event handlers) ------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Handle right-click context menu events on the scene.
        Prioritizes item-specific handlers before showing the general menu.
        """

        # Call super-class event-handler first:
        super().contextMenuEvent(event)
        if event.isAccepted():
            return

        # 1. Store scene-position (do not remove).
        # 2. Open menu at cursor position:
        self._cpos = event.scenePos().toPoint()
        self._menu.exec(event.screenPos())
        event.accept()

    def mouseMoveEvent(self, event):
        """
        Handle mouse movement to draw a live connector if a transient connection is active.
        """

        if self._transient.origin:
            cpos = event.scenePos()
            opos = self._transient.origin().scenePos()
            self._transient.connector.draw(opos, cpos, PathGeometry.BEZIER)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Finalize a connector between handles upon mouse release, if valid.
        """

        # If there is no transient connection being drawn, call super-class implementation and return:
        if (
            not self._transient.active or
            event.button() != Qt.MouseButton.LeftButton
        ):
            super().mouseReleaseEvent(event)
            return

        # Begin event handling: First, check if the user is trying to create a connection between two nodes:
        tpos = event.scenePos()                         # Cursor coordinate at mouse-release (scene's frame of reference)
        node = self._transient.origin().parentItem()    # Parent node of the transient connector's origin handle

        # If item below cursor is an Anchor...:
        item = self.itemAt(tpos, QTransform())
        if isinstance(item, Anchor):

            # Verify that origin and target nodes are different:
            if item.parentItem() == node:
                self.reset_connection()
                return

            # Create handle at the position:
            apos = item.mapFromScene(tpos)                      # Map scene-coordinate to anchor's local coordinate system
            item.sig_item_clicked.emit(QPointF(0, apos.y()))    # Emit signal to trigger handle creation

        # Use scene.itemAt() again, but this time, the newly created handle should be returned:
        origin = self._transient.origin
        target = self.itemAt(tpos, QTransform())
        if (
                not isinstance(target, Handle) or
                target.parentItem() == node or
                target.connected or
                origin == target
        ):
            self.reset_connection()
            return

        # Connect the origin and target with a connector:
        connector = Connector(None, origin=origin(), target=target, symbol=self.unique_symbol())
        connector.sig_item_removed.connect(self.on_item_removed)

        action = ConnectHandleAction(self, connector)
        self.manager.do(action)

        self.reset_connection()
        super().mouseReleaseEvent(event)

    # CANVAS (User-actions) --------------------------------------------------------------------------------------------

    def create_node(self, **kwargs):
        """
        Create a new node at the current or given position and push the action to the undo stack.

        :param kwargs: May include 'cpos' for position and 'name' for node label.
        """

        # Redefine node-attribute(s):
        cpos = kwargs.get("cpos") if "cpos" in kwargs.keys()    else self._cpos     # Scene-position of the node
        name = kwargs.get("name") if "name" in kwargs.keys()    else "Node"         # Name of the node
        push = kwargs.get("push") if "push" in kwargs.keys()    else True           # Push node-creation to undo-stack

        # Create node, connect signals:
        node = Node(cpos, name)
        node.uid = 'N' + str(self.node_total).zfill(4)
        self.node_total += 1

        node.sig_execute_action.connect(self.on_execute_action)
        node.sig_handle_clicked.connect(self.start_connection)
        node.sig_handle_removed.connect(self.on_item_removed)

        # Add to scene and operatio):
        if push:
            actions = CreateNodeAction(self, node)
            self.manager.do(actions)

        return node

    def create_source(self, **kwargs):
        """
        Create a new resource stream.
        """

        # Define source-attribute(s):
        cpos = kwargs.get("cpos") if "cpos" in kwargs.keys() else self._cpos
        name = kwargs.get("name") if "name" in kwargs.keys() else "Resource"
        push = kwargs.get("push") if "push" in kwargs.keys() else True           # Push node-creation to undo-stack

        # Create source:
        item = Stream(None, name, StreamType.OUT)
        item.setPos(cpos.toPointF())

        # Connect signals to slots:
        item.sig_socket_clicked.connect(self.start_connection)
        item.sig_stream_deleted.connect(self.on_item_removed)

        # Add to scene and operation:
        if push:
            actions = CreateStreamAction(self, item)
            self.manager.do(actions)

        return item

    def create_sink(self, **kwargs):
        """
        Create a new resource stream.
        """

        # Define source-attribute(s):
        cpos = kwargs.get("cpos") if "cpos" in kwargs.keys() else self._cpos
        name = kwargs.get("name") if "name" in kwargs.keys() else "Resource"
        push = kwargs.get("push") if "push" in kwargs.keys() else True           # Push node-creation to undo-stack

        # Create source:
        item = Stream(None, name, StreamType.INP)
        item.setPos(cpos.toPointF())

        # Connect signals to slots:
        item.sig_socket_clicked.connect(self.start_connection)
        item.sig_stream_deleted.connect(self.on_item_removed)

        # Add to scene and operation:
        if push:
            actions = CreateStreamAction(self, item)
            self.manager.do(actions)

        return item

    def copy(self):
        """
        Copies selected items to an internal clipboard and dims their appearance.
        """

        # Copy all items to clipboard:
        Canvas.Global.clipboard = set(self.selectedItems().copy())

        # Make copied node_items translucent:
        for item in Canvas.Global.clipboard:
            if isinstance(item, (Node, Stream)):
                item.setOpacity(0.6)

    def paste(self):
        """
        Pastes copied nodes and re-establishes valid handle connections between them.
        """

        # Return if clipboard is empty:
        if not Canvas.Global.clipboard:
            print(f"Canvas.paste(): Nothing to paste!")
            return

        # Initialize batch-actions:
        batch = BatchActions([])

        # Log:
        print(f"Pasting items to canvas: {self.objectName()}")

        # Paste from clipboard:
        for item in Canvas.Global.clipboard:

            if isinstance(item, Node):

                # Duplicate node and connect signals:
                node, actions = item.duplicate(self)
                node.uid = 'N' + str(self.node_total).zfill(4)
                node.setSelected(True)
                self.node_total += 1

                node.sig_execute_action.connect(self.on_execute_action)
                node.sig_handle_clicked.connect(self.start_connection)
                node.sig_handle_removed.connect(self.on_item_removed)

                # Add actions to batch:
                batch.add_to_batch(actions)

                # Unselect copied node_items and reset opacity:
                item.setSelected(False)
                item.setOpacity(1.0)

            elif isinstance(item, Stream):

                # Duplicate source/sink and connect signals:
                stream, action = item.duplicate(self)
                stream.setSelected(True)
                stream.sig_socket_clicked.connect(self.start_connection)
                stream.sig_stream_deleted.connect(self.on_item_removed)

                # Add actions to batch:
                batch.add_to_batch(action)

                # Reset state:
                item.setSelected(False)
                item.setOpacity(1.0)

        # Re-establish connections:
        while Handle.cmap:

            try:
                # `handle` and `conjugate` belong to the copied nodes. `origin` and `target` are their mirrors in the
                # copied nodes that must now be connected:
                handle   , origin = Handle.cmap.popitem()
                conjugate, target = handle.conjugate(), Handle.cmap[handle.conjugate()]     # Throws exception if `handle` is not connected

                # If exception is not thrown, both origin and target are valid, connected handles:
                Handle.cmap.pop(conjugate)  # Remove the key corresponding to handle's conjugate

                # Create connector and add it to batch:
                connector = Connector(None, origin=origin, target=target, symbol=self.unique_symbol())
                connector.sig_item_removed.connect(self.on_item_removed)

                # Add connector to the dictionary here, so that self.unique_symbol() returns unique symbols:
                self.edge_items[connector] = True

                # Add connector-creation to batch:
                batch.add_to_batch(ConnectHandleAction(self, connector))

            except KeyError as key_error:       # Thrown by `Handle.cmap`
                print(key_error)
                pass

            except TypeError as type_error:     # Thrown by `handle`
                print(type_error)
                pass

        # Execute batch operations:
        self.manager.do(batch)

    def clear(self):
        """
        Clears the canvas after user confirmation and wipes the undo stack.
        """

        if len(self.items()) <= 1:
            message = Dialog(QtMsgType.QtInfoMsg,
                             "No items in the scene!")
            message.exec()
            return

        # Confirm clear:
        dialog = Dialog(QtMsgType.QtWarningMsg,
                        "This action cannot be undone. Are you sure?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        if dialog.exec() == QMessageBox.StandardButton.Yes:

            # Delete nodes and streams:
            self.delete_items(set(self.node_items.keys()))
            self.delete_items(set(self.flow_items.keys()))

            # Safe-delete undo and redo stacks:
            self.manager.wipe_stack()

            # Notify viewer:
            self.sig_canvas_cleared.emit()

    def group(self):

        if not len(self.selectedItems()):
            return

        dialog = QInputDialog(None)
        dialog.setLabelText("Enter group label:")

        text, ok = QInputDialog.getText(None, "Enter Name", "Group Name:")
        if ok and text:
            print("User entered:", text)

    def group_flows(self, _label, generate_eqn = False):

        items    = set()
        equation = str(f"TOTAL_{_label}")

        for flow in self.flow_items.keys():
            if (
                    flow.isVisible() and
                    flow.label == _label and
                    flow.socket.connector is not None
            ):
                items.add(flow)
                equation += f" - {flow.socket.connector().symbol}"

        equation += " = 0.0;"
        return items, equation if generate_eqn else None


    def import_json(self):
        """
        Opens a file dialog to import a schematic from a JSON file.
        """

        path = QFileDialog.getOpenFileName(None, "Open File", "", "JSON files (*.json)")
        if path[0] == "":
            return

        file = Path(path[0])        # Open JSON-file
        code = file.read_text()     # Read contents

        # Generate schematic from JSON:
        JsonLib.decode_json(code, self, group_actions=True)

    def export_json(self):
        """
        Opens a file dialog to export the current schematic to a JSON file.
        """

        root = JsonLib.encode_json(self)
        path = QFileDialog.getSaveFileName(None, "Save File", "", "JSON files (*.json)")
        if not bool(path[0]):
            return

        file = Path(path[0])
        file.write_text(root)

    def select_items(self, item_set: set):
        """
        Marks items in the provided set as selected, if they belong to the scene.

        :param item_set: A set of QGraphicsObject instances to be selected.
        """

        for item in item_set:
            if isinstance(item, QGraphicsObject) and item.scene() == self:  # Check if item belongs to the scene
                item.setSelected(True)

    def delete_items(self, items: set):
        """
        Deletes nodes and their handles from the canvas using batched undoable actions.

        :param items: A set of items (typically nodes) to delete.
        """

        # Create batch-commands:
        batch = BatchActions([])

        # Construct batch commands:
        for item in items:
            if isinstance(item, Node):
                total = item[StreamType.INP] | item[StreamType.OUT]
                for handle in total:
                    if total[handle]:
                        batch.add_to_batch(RemoveHandleAction(item, handle))

                batch.add_to_batch(RemoveNodeAction(self, item))

            elif isinstance(item, Stream):
                batch.add_to_batch(RemoveStreamAction(self, item))

        # Execute:
        if batch.size():    self.manager.do(batch)

    def on_execute_action(self, action: AbstractAction):
        if isinstance(action, AbstractAction):
            self.manager.do(action)

    def start_connection(self, handle: Handle):
        """
        Begin a transient connection starting from the specified handle.

        :param handle: The handle from which the connection starts.
        """

        # If a transient is already active, abort!
        if self._transient.active:
            return

        self._transient.active = True
        self._transient.origin = weakref.ref(handle)

        self._transient.connector.show()
        self.update()

    def reset_connection(self):
        """
        Cancels and clears the current transient connection path.
        """

        self._transient.active = False
        self._transient.origin = None
        self._transient.target = None

        self._transient.connector.clear()
        self.update()

    # CANVAS (PyQt6 Slots) ---------------------------------------------------------------------------------------------

    @pyqtSlot()
    @pyqtSlot(QGraphicsObject)
    def on_item_removed(self, item: QGraphicsObject | None = None):
        """
        Slot triggered when an emits a 'sig_item_removed' signal. Deletes the node.
        """

        item = self.sender()                    # Get signal-emitter
        if isinstance(item, (Node, Stream)):    # Type-check
            self.delete_items({item})           # Delete node

    # Returns node corresponding to `uid`:
    def find_node_by_uid(self, uid: str):
        for item in self.items():
            if isinstance(item, Node) and item.uid == uid:
                return item

        return None

    # CANVAS (Properties) ----------------------------------------------------------------------------------------------
    # Properties:

    # Read-only:
    @property
    def menu_position(self):
        """
        Returns the last-known context menu position
        """
        return self._cpos

    # Read-only:
    @property
    def node_count(self):
        """
        Returns the number of active (i.e. visible) nodes in the scene:
        """

        count = sum(1 for node in self.node_items if node.Visible())
        return count

    # Read-only:
    @property
    def edge_count(self):
        """
        Returns the number of active (i.e. visible) connectors in the scene:
        """

        count = sum(1 for connector in self.edge_items if connector.Visible())
        return count

    # UTILITY ----------------------------------------------------------------------------------------------------------

    def unique_symbol(self):

        prefix  = "X"
        indices = set()

        for connector in self.edge_items:
            if connector.isEnabled():
                indices.add(int(connector.symbol.split('X')[1]))

        if not indices:
            return prefix + "0"

        sequence = set(range(0, max(indices) + 2))
        reusable = sequence - indices

        return prefix + str(min(reusable))


