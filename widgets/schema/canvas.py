from pathlib         import Path
from PyQt6.QtGui     import *
from PyQt6.QtCore    import *
from PyQt6.QtWidgets import *

from widgets.schema         import JsonLib
from widgets.schema.graph   import *

class Canvas(QGraphicsScene):

    # Global lists:
    nodes = list()
    edges = list()

    # Signals:
    sig_canvas_updated = pyqtSignal()       # Emitted when items in the scene are added, modified, or deleted

    # Reusable connector for temporarily connecting nodes:
    class Meta:
        active = False
        origin = None
        target = None
        connector = Connector()

    # Initializer:
    def __init__(self, rect: QRectF, parent: QObject):

        # Initialize base-class:
        super().__init__(rect, parent)

        # Initialize context-menu:
        self.__menu__()

        # Metadata:
        self._file = ""
        self._meta = self.Meta()
        self.addItem(self._meta.connector)

        # Create default categories:
        Category.List.append(Category("Default", QColor(Qt.GlobalColor.darkGray)))
        Category.List.append(Category("Energy", QColor(0xffba49)))
        Category.List.append(Category("Mass", QColor(0x0eb1d2)))
        Category.List.append(Category("Power", QColor(0x42113c)))

        # Behaviour and attrib:
        self.setSceneRect(rect)
        self.setBackgroundBrush(QColor(0xeeeeee))

    # Context-menu initializer:
    def __menu__(self):

        # Create menu:
        self.__menu = QMenu()

        # Submenu for creating nodes:
        self.__subm = self.__menu.addMenu("Create Node")
        __node = self.__subm.addAction("Default")
        __src  = self.__subm.addAction("Source")
        __sink = self.__subm.addAction("Sink")

        # Open and save actions:
        self.__menu.addSeparator()
        __open = self.__menu.addAction("Open Schematic")
        __save = self.__menu.addAction("Save Schematic")

        # Group actions:
        self.__menu.addSeparator()
        __group = self.__menu.addAction("Group Items")
        __clear = self.__menu.addAction("Clear Scene")
        __close = self.__menu.addAction("Quit")

        # Connect actions to handlers:
        __node.triggered.connect(self.create_node)
        __open.triggered.connect(self.import_json)
        __save.triggered.connect(self.export_json)

        __clear.triggered.connect(self.delete)

        # Behaviour:
        self.__menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.__subm.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

    # Event-handler for context menus:
    def contextMenuEvent(self, event):

        # Prioritize handling by scene-items:
        super().contextMenuEvent(event)
        if event.isAccepted():
            return

        self.__menu.exec(event.screenPos())  # Open menu
        event.accept()  # Accept event to stop further processing

    # Event-handler for mouse-clicks:
    def mousePressEvent(self, event):
        # Prioritize event-handling by scene-objects:
        super().mousePressEvent(event)
        if event.isAccepted():
            return

        if self.itemAt(event.scenePos(), QTransform()) is None:
            self.clearSelection()

    # Event-handler for mouse-move events:
    def mouseMoveEvent(self, event):

        # If a connection is being drawn, connect the endpoints:
        if self._meta.active:
            origin = self._meta.origin.scenePos()
            target = event.scenePos()

            # Connect endpoints:
            self._meta.connector.connect(origin, target)

        super().mouseMoveEvent(event)
        event.accept()

    # Event-handler for mouse-release:
    def mouseReleaseEvent(self, event):

        if event.button() != Qt.MouseButton.LeftButton or not self._meta.active:
            super().mouseReleaseEvent(event)
            return

        # Get coordinates:
        tpos = event.scenePos()
        opos = self._meta.origin.scenePos()
        node = self._meta.origin.parentItem()

        item = self.itemAt(tpos, QTransform())
        if isinstance(item, Anchor):

            if item.parentItem() == node:
                self.reset_transient()
                return

            apos = item.mapFromScene(tpos)
            item.sig_item_clicked.emit(QPointF(0, apos.y()), False)

        origin = self._meta.origin
        target = self.itemAt(tpos, QTransform())
        if not isinstance(target, Handle) or \
                origin == target or \
                target.connected:
            self.reset_transient()
            return

        connector = Connector(self._meta.origin, target)
        connector.sig_item_deleted.connect(self.on_item_deleted)

        self.edges.append(connector)
        self.addItem(connector)
        self.reset_transient()

    # Node-creator:
    @pyqtSlot(name="Node Creator")
    def create_node(self, name: str = "Node", coordinate: QPoint = QPointF()):

        # If coordinates haven't been provided, get cursor position in scene-coordinates:
        port = self.views()
        cpos = QCursor.pos()
        if coordinate == QPointF() and port:
            coordinate = port[0].mapToScene(cpos)

        # Create new node
        node = Node(name)
        node.setPos(coordinate)

        # Add node to scene and emit signal:
        self.addItem(node)
        self.nodes.append(node)
        self.sig_canvas_updated.emit()

        # Return reference to created node:
        return node

    # Draw transient:
    @pyqtSlot(Handle, name="Draw Connector")
    def start_connection(self, handle: Handle):

        if not isinstance(handle, Handle):
            return

        self._meta.active = True
        self._meta.origin = handle

    # Reset transient:
    @pyqtSlot()
    def reset_transient(self):
        self._meta.active = False
        self._meta.origin = None
        self._meta.connector.clear()

    @pyqtSlot()
    # Duplicates all selected nodes:
    def copy(self):

        # Reset the hash-map:
        Handle.cmap = {}

        if not len(self.selectedItems()):
            print(f"INFO: No items in the clipboard!")
            return

        # Loop over selected nodes and duplicate them:
        for item in self.selectedItems():

            if isinstance(item, Node):
                node = item.duplicate()  # Duplicating the node populates Handle.cmap
                node.setSelected(True)  # Select the pasted nodes
                item.setSelected(False)  # Deselect the copied nodes

                self.addItem(node)  # Add node to scene
                self.nodes.append(node)  # Add node to list

        # Re-establish connections:
        while Handle.cmap:

            try:
                handle, origin = Handle.cmap.popitem()
                conjugate, target = handle.conjugate, Handle.cmap[handle.conjugate]  # May throw exception

                # If exception is not thrown, then both origin and target are valid:
                Handle.cmap.pop(conjugate)  # Remove the key corresponding to handle's conjugate

                connector = Connector(origin, target)
                connector.sig_item_deleted.connect(self.on_item_deleted)

                self.edges.append(connector)
                self.addItem(connector)

            except KeyError as key_error:
                pass

        Handle.cmap = {}  # Clear copy-map
        self.sig_canvas_updated.emit()  # Trigger database-update

    @pyqtSlot()
    # Display graph-information:
    def info(self):

        print("")
        print("--------------")
        print("Graph Overview")
        print("--------------")

        print(f"NODES: {len(self.nodes)}")
        for node in self.nodes:
            print(f"- {node.nuid()}:")
            for handle in (node[Stream.INP] + node[Stream.OUT]):
                print(f"\t{handle.id} is of type {handle.category}")

        print("")
        print(f"EDGES: {len(self.edges)}")
        for connection in self.edges:
            print(f"- {connection.nuid()} connects {connection.origin.nuid()} and {connection.target.nuid()}")

    @pyqtSlot()
    # Select all nodes:
    def select(self):
        items = self.items()  # Get all items in the scene:
        for item in items:
            if isinstance(item, Node):  # Filter nodes
                item.setSelected(True)  # Select them

    @pyqtSlot()
    # Delete all nodes:
    def delete(self):

        items = self.items()
        for item in items:
            if isinstance(item, Node):
                item.delete()

    @pyqtSlot()
    # Clear references when node is deleted:
    def on_item_deleted(self):

        item = self.sender()
        if isinstance(item, Node):
            self.nodes.remove(item)
            self.removeItem(item)

        elif isinstance(item, Connector):
            print(f"Deleting {item.nuid()}")
            self.edges.remove(item)
            self.removeItem(item)

        # Trigger database update:
        self.sig_canvas_updated.emit()

    # Find node by nuid:
    def find_by_nuid(self, nuid: str):

        for node in self.nodes:
            if node.nuid() == nuid:
                return node

        return None

        # Find node by nuid:

    # Find node by name:
    def find_by_name(self, name: str):

        nodes = list()
        for node in self.nodes:
            if node.name() == name:
                nodes.append(node)

        if len(nodes):
            return nodes

        else:
            return None

    # New project:
    def new_project(self):

        path = QFileDialog.getSaveFileName(None, "New File", "", "JSON files (*.json)")
        if path[0] == "":
            return

        self._file = Path(path[0]).name

    # Json read:
    def import_json(self):

        path = QFileDialog.getOpenFileName(None, "Open File", "", "JSON files (*.json)")
        if path[0] == "":
            return

        file = Path(path[0])
        code = file.read_text()
        self._file = file.name

        try:
            JsonLib.decode_json(code, self)

        except Exception as exception:
            print(f"An exception occurred: {exception}")

    # Json write:
    @staticmethod
    def export_json(self):

        root = JsonLib.encode_json()
        path = QFileDialog.getSaveFileName(None, "Save File", "", "JSON files (*.json)")
        if not bool(path[0]):
            return

        file = Path(path[0])
        file.write_text(root)

    # AMPL script:
    def script_ampl(self):

        script = ""
        preface = "# AMPL script created with Climact.ai\n"

        vardecl = "\n# Variables\n"
        pardecl = "\n# Parameters\n"
        eqndecl = "\n# Constraints\n"

        for node in self.nodes:
            prefix = node.nuid().split('#')
            prefix = prefix[0] + prefix[1]
            for par in node[Stream.PAR]:
                if par.value is not None:
                    pardecl += f"param {prefix}_{par.symbol} = {par.value};\n"
                else:
                    vardecl += f"var {prefix}_{par.symbol};\n"

        script = preface + pardecl + vardecl + eqndecl
        return script