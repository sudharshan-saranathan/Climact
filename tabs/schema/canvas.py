#-----------------------------------------------------------------------------------------------------------------------
# Author: Sudharshan Saranathan
# GitHub: https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (pip install PyQt6),
#             google-genai (pip install google-generative-ai)
#-----------------------------------------------------------------------------------------------------------------------
import logging
import weakref
import qtawesome as qta

from dataclasses import dataclass
from PyQt6.QtGui import (
    QIcon,
    QBrush,
    QColor,
    QAction,
    QTransform, QKeySequence
)
from PyQt6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QObject,
    pyqtSlot,
    pyqtSignal,
    QtMsgType
)
from PyQt6.QtWidgets import (
    QMenu,
    QFileDialog,
    QMessageBox, 
    QApplication,
    QGraphicsScene,
    QGraphicsObject
)

from .graph   import *
from .jsonlib import JsonLib

from util    import random_id, random_hex
from enum    import Enum
from custom  import *
from actions import *

# Enum for SaveState:
class SaveState(Enum):
    EXPORTED = 0
    MODIFIED = 1
    ERROR    = 2

# Class Canvas - Subclass of QGraphicsScene, manages graphical items:
class Canvas(QGraphicsScene):
    """
    Manage graphical items, connections, and user interactions within a 2D scene.

    The Canvas class is a central component for creating and manipulating visual
    representations of data flows, schematics, or diagrams. It handles the
    creation, deletion, and interaction of nodes, terminals (input/output points),
    and connectors. It also manages the overall state of the canvas, including
    saving and loading schemas from JSON files, and supports undo/redo functionality
    through an actions-manager.

    Key functionalities include:
    - Creating and managing nodes, terminals, and connectors.
    - Handling user input events such as mouse clicks, moves, and context menu requests.
    - Implementing a transient connector for interactively drawing connections.
    - Supporting copy, paste, and deletion of items.
    - Importing and exporting canvas schematics in JSON format.
    - Managing the save state of the canvas (saved/unsaved).
    - Emitting signals for various canvas events (item creation/removal, state changes).

    Attributes:
        actions (BatchActions): Manages batch operations for undo/redo.
        Manager (ActionsManager): Manages the undo/redo stack.
        Term_db (dict): Registry of terminals on the canvas.
        Node_db (dict): Registry of nodes on the canvas.
        Conn_db (dict): Registry of connectors on the canvas.
        Type_db (set): Set of defined stream types (e.g., Mass, Energy).
    """

    # Signals:
    sig_node_clicked = pyqtSignal()             # Emitted when an item is double-clicked.
    sig_item_created = pyqtSignal()             # Emitted when a new item is created.
    sig_item_removed = pyqtSignal()             # Emitted when an item is removed.
    sig_canvas_reset = pyqtSignal()             # Emitted when the canvas is reset.
    sig_schema_setup = pyqtSignal(str)          # Emitted when a JSON schematic is loaded.
    sig_canvas_state = pyqtSignal(SaveState)    # Emitted when the canvas's state changes.

    # Placeholder-connector:
    class Transient:
        def __init__(self):
            self.active = False                 # Set to True when the user is drawing a connection, False otherwise.
            self.origin = None                  # Reference pointer to the connector's origin (tabs/schema/graph/handle.py).
            self.target = None                  # Reference pointer to the connector's target (tabs/schema/graph/handle.py).
            self.connector = Connector(str())   # Connector object (tabs/schema/graph/connector.py).

    # Global registry:
    @dataclass
    class Registry:
        clipboard = list()

    # CANVAS (Initializers) --------------------------------------------------------------------------------------------
    # Instance initializer:
    def __init__(self, bounds: QRectF, parent: QObject | None = None):

        # Initialize super-class:
        super().__init__(bounds, parent)

        # Initialize actions-manager:
        self.actions = BatchActions([])
        self.manager = ActionsManager()

        # Convenience variables:
        self._ntot = 0
        self._rect = bounds
        self._cpos = QPointF()
        self._conn = Canvas.Transient()
        self.state = SaveState.MODIFIED

        # Add the transient-connector to the scene:
        self.addItem(self._conn.connector)

        # Customize attribute(s):
        self.setSceneRect(self._rect)
        self.setBackgroundBrush(QBrush(0xefefef, Qt.BrushStyle.DiagCrossPattern))
        self.setObjectName(random_id(length=4, prefix='S'))

        # Initialize registries:
        self.term_db = dict()  # Maps each terminal to a bool indicating whether it's currently visible/enabled.
        self.node_db = dict()  # Maps each _node to a bool indicating whether it's currently visible/enabled.
        self.conn_db = dict()  # Maps each connector to a bool indicating whether it's currently visible/enabled.
        self.type_db = set()   # List of defined stream-types (e.g., Mass, Energy, Electricity, etc.)

        # Add default streams:
        self.type_db.add(Stream("Default", Qt.GlobalColor.darkGray))   # Default
        self.type_db.add(Stream("Energy", QColor("#F6AE2D")))          # Energy
        self.type_db.add(Stream("Power", QColor("#474973")))           # Power
        self.type_db.add(Stream("Mass", QColor("#028CB6")))            # Mass

        # Initialize menu:
        self._init_menu()

    # Context-menu initializer:
    def _init_menu(self):
        """
        Initializes the canvas's context menu. Actions in the menu include _node- and terminal-creation, import and
        export from/to JSON files, and group/clear operations. This method is called once by the class's initializer.
        """

        # Create menu:
        self._menu = QMenu()                                # Main context-menu.
        self._subm = self._menu.addMenu("Create Objects")   # Submenu for creating items.

        # Submenu for creating scene-items:
        _node = self._subm.addAction(qta.icon("ph.cpu", color="darkblue"),
                                     "Node", QKeySequence("Ctrl+N"), self.create_node)

        _tout = self._subm.addAction(qta.icon("ph.plus", color="darkgreen"),
                                     "Terminal (Inp)",
                                     QKeySequence("Ctrl+["),
                                     lambda: self.create_terminal(EntityClass.OUT,self._cpos))  # Action to create a new output terminal

        _tinp = self._subm.addAction(qta.icon("ph.minus", color="darkred"),
                                     "Terminal (Out)",
                                     QKeySequence("Ctrl+]"),
                                     lambda: self.create_terminal(EntityClass.INP,self._cpos))  # Action to create a new output terminal

        # Import and export actions:
        self._menu.addSeparator()
        _load = self._menu.addAction(qta.icon("mdi.folder", color="darkgray"), "Import Schema", QKeySequence.StandardKey.Open, self.import_schema)
        _save = self._menu.addAction(qta.icon("mdi.content-save", color="darkgreen"), "Export Schema", QKeySequence.StandardKey.Save, self.export_schema)

        # Actions for cloning and pasting items:
        self._menu.addSeparator()
        _undo  = self._menu.addAction(qta.icon("mdi.undo", color="black"), "Undo", QKeySequence.StandardKey.Undo)
        _redo  = self._menu.addAction(qta.icon("mdi.redo", color="black"), "Redo", QKeySequence.StandardKey.Redo)
        _clone = self._menu.addAction(qta.icon("mdi.content-copy", color="lightblue"), "Clone", QKeySequence.StandardKey.Copy)
        _paste = self._menu.addAction(qta.icon("mdi.content-paste", color="orange"), "Paste", QKeySequence.StandardKey.Paste)

        # Actions for selecting and deleting items:
        self._menu.addSeparator()
        _select = self._menu.addAction(qta.icon("mdi.select", color="magenta"), "Select All", QKeySequence.StandardKey.SelectAll)
        _delete = self._menu.addAction(qta.icon("mdi.delete", color="red"), "Delete", QKeySequence.StandardKey.Delete)

        # Group and Clear actions:
        self._menu.addSeparator()
        _group = self._menu.addAction(qta.icon("mdi.layers", color="teal"), "Group Items", QKeySequence("Ctrl+G"), lambda: print(f"Grouping selected items"))
        _clear = self._menu.addAction(qta.icon("mdi.eraser", color="darkred"), "Clear Scene", QKeySequence("Ctrl+E"), self.clear)
        _exit  = self._menu.addAction(qta.icon("mdi.power", color="black"), "Quit" , QKeySequence.StandardKey.Quit,  QApplication.quit)

        # Show icons:
        _node.setIconVisibleInMenu(True)
        _load.setIconVisibleInMenu(True)
        _save.setIconVisibleInMenu(True)
        _undo.setIconVisibleInMenu(True)
        _redo.setIconVisibleInMenu(True)
        _exit.setIconVisibleInMenu(True)
        _tout.setIconVisibleInMenu(True)
        _tinp.setIconVisibleInMenu(True)
        _clone.setIconVisibleInMenu(True)
        _paste.setIconVisibleInMenu(True)
        _select.setIconVisibleInMenu(True)
        _delete.setIconVisibleInMenu(True)

        # Make shortcuts visible:
        _node.setShortcutVisibleInContextMenu(True)
        _tout.setShortcutVisibleInContextMenu(True)
        _tinp.setShortcutVisibleInContextMenu(True)
        _load.setShortcutVisibleInContextMenu(True)
        _save.setShortcutVisibleInContextMenu(True)
        _undo.setShortcutVisibleInContextMenu(True)
        _redo.setShortcutVisibleInContextMenu(True)

        _select.setShortcutVisibleInContextMenu(True)
        _delete.setShortcutVisibleInContextMenu(True)

        _clone.setShortcutVisibleInContextMenu(True)
        _paste.setShortcutVisibleInContextMenu(True)
        _exit .setShortcutVisibleInContextMenu(True)

        _group.setShortcutVisibleInContextMenu(True)
        _clear.setShortcutVisibleInContextMenu(True)

        _group.setIconVisibleInMenu(True)
        _clear.setIconVisibleInMenu(True)

    # Event-Handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. contextMenuEvent       Handles context-menu events (triggered when the user right-clicks on the canvas).
    # 2. mouseMoveEvent         If a connection is active, this event will continuously update the connector's path.
    # 3. mouseReleaseEvent      If a connection is active and the mouse-button was released at a target _node's anchor,
    #                           this event will create a new handle and establish a connection between the origin and 
    #                           target.
    # ------------------------------------------------------------------------------------------------------------------

    # Context-menu event handler:
    def contextMenuEvent(self, event):
        """
        Opens the canvas's context-menu when the user right-clicks on the canvas.

        Args: 
            event (QGraphicsSceneContextMenuEvent): Event instance, internally propagated and managed by Qt.

        Returns: 
        None
        """

        # Call super-class implementation first:
        super().contextMenuEvent(event)
        if event.isAccepted() or self._menu is None:    return

        # 1. Store scene-position (do not remove).
        # 2. Open the menu at the cursor position:
        self._cpos = event.scenePos()
        self._menu.exec(event.screenPos())
        event.accept()

    def mouseMoveEvent(self, event):
        """
        Re-implementation of QGraphicsScene.mouseMoveEvent(). When an active connection is being drawn, this handler
        will re-compute and draw the connector's path as the cursor is dragged across the canvas. In the absence of 
        an active connection, the handler will forward the event to the super-class.

        :param: event (QGraphicsSceneMouseEvent): Event instance, internally propagated and managed by Qt.
        """

        # Forward event to other handlers:
        super().mouseMoveEvent(event)

        # If the transient-connector is active, update its path:
        if  self._conn.active:
            self._conn.connector.draw(self._conn.origin().scenePos(), 
                                      event.scenePos(), 
                                      PathGeometry.HEXAGON
                                      )

        # Store the cursor position in scene-coordinates:
        self._cpos = event.scenePos()  # Update the cursor position in scene-coordinates.

    def mouseReleaseEvent(self, event):
        """
        Re-implementation of QGraphicsScene.mouseReleaseEvent(). If a connection was being drawn when this event is 
        triggered, and if certain conditions are met, this method will create a new target-handle and establish a 
        connection between the origin and target handles. The method includes various checks to prevent logically
        invalid connections (such as from one _node or handle to itself).
        
        :param: event (QGraphicsSceneMouseEvent): Event instance, internally propagated by Qt.
        """
    
        # If the transient-connector is inactive or the release event is not a left-click, forward event to super-class:
        if (
            not self._conn.active or 
            event.button() != Qt.MouseButton.LeftButton
        ):
            # Forward event to super-class and return:
            super().mouseReleaseEvent(event)
            return

        # Define convenience variables:
        _tpos = event.scenePos()                    # Release-position in scene-coordinates.
        _node = self._conn.origin().parentItem()    # Origin handle's parent item (could be a _node or a terminal).

        # Find the QGraphicsObject at the cursor's click-position:
        _item = self.itemAt(event.scenePos(), QTransform())

        # If the item below the cursor is an anchor, create a new handle at the target anchor:
        if isinstance(_item, Anchor):

            # Verify that the target anchor's parent _node is different from the origin handle's parent _node:
            if (
                _node == _item.parentItem() or
                _item.stream() == self._conn.origin().eclass
            ):
                self.reset_transient()
                super().mouseReleaseEvent(event)
                return

            # Create a new handle at the target anchor:
            _apos = _item.mapFromScene(_tpos)       # Convert scene-coordinates to anchor-coordinates.
            _apos = QPointF(0, _apos.y())           # Set x-coordinate to 0.
            _item.sig_item_clicked.emit(_apos)      # Emit signal to create a new handle.

        # Define convenience variables:
        origin = self._conn.origin()               # Origin handle is set in `self.begin_transient()`
        target = self.itemAt(_tpos, QTransform())  # This should return the new handle created at the target anchor.

        # Abort-conditions:
        if (
            not isinstance(target, Handle) or
            target.connected or
            origin == target or
            origin.eclass == target.eclass or
            origin.parentItem() == target.parentItem()
        ):
            self.reset_transient()
            super().mouseReleaseEvent(event)
            return

        # Create a new connection between the origin and target and add it to the canvas:
        _connector = Connector(self.create_cuid(), origin, target)
        self.conn_db[_connector] = EntityState.ACTIVE
        self.addItem(_connector)

        # Push action to undo-stack:
        self.manager.do(ConnectHandleAction(self, _connector))

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.MODIFIED)

        # Reset transient-connector:
        self.reset_transient()

        # Forward event to super-class:
        super().mouseReleaseEvent(event)

    # Custom Methods ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 01. create_node           Creates a new _node with a single connection point.
    # 02. connect_node_signals  Connects the _node's signals to appropriate slots for state management.
    # 03. create_terminal       Creates a new terminal (input or output) at a specified position.
    # 04. create_cuid           Creates a unique ID for a new connector.
    # 05. create_nuid           Creates a unique ID for a new _node.
    # 06. store                 Adds selected items to the clipboard.
    # 07. clone                 Clones the clipboard's contents and adds them to the canvas.
    # 08. paste_item            Pastes a _node or terminal item onto the canvas.
    # 09. select_items          Selects items in the canvas based on a dictionary of items.
    # 10. delete_items          Deletes items from the canvas using undoable batch-actions.
    # 11. symbols               Return a list of symbols from the canvas's _nodes and connectors.
    # 12. import_schema         Reads a JSON schematic and populates the canvas with the schematic's contents.
    # 13. export_schema         Saves the canvas's contents as a JSON schematic.
    # 14. begin_transient       Begins a transient connection by setting the origin handle and activating the connector.
    # ------------------------------------------------------------------------------------------------------------------

    # Create a new node and add it to the scene:
    def create_node(self,
                    name: str = "Node",
                    cpos: QPointF | None = None,
                    push: bool = True
                    ):
        """
        Create a new _node and add it to the canvas.
        :param name: Name of the node to be created. Default is "Node".
        :param cpos: Position of the node in scene-coordinates. If `None`, the last-displayed position of the context menu is used.
        :param push: Whether to push the creation action to the undo-stack. Default is `True`.
        :return:
        """

        # Create a new _node and assign a unique-identifier:
        _node = Node(
            name,
            cpos or self._cpos,
            uid = self.create_nuid()
        )

        # Add the created node to the database, and to the QGraphicsScene:
        self.node_db[_node] = EntityState.ACTIVE
        self.addItem(_node)

        # Push to undo stack (if required):
        if push:   self.manager.do(CreateNodeAction(self, _node))

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.MODIFIED)

        # Return reference to newly created _node:
        return _node

    def connect_node_signals(self, _node: Node):

        # Type-check:
        if not isinstance(_node, Node): raise TypeError(f"Argument `_node` must be of type `Node`")

        # Connect the _node's signals to appropriate slots:
        _node.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED))
        _node.sig_exec_actions.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED))
        _node.sig_exec_actions.connect(self.manager.do)
        _node.sig_item_removed.connect(self.on_item_removed)
        _node.sig_handle_clicked.connect(self.begin_transient)

    def create_terminal(self,
                        _eclass: EntityClass,       # EntityClass (INP or OUT), see custom/entity.py.
                        _coords: QPointF = None,    # Position of the terminal (in scene-coordinates).
                        _flag  : bool = True        # Should the action be pushed to the undo-stack?
                        ):
        """
        Create a new terminal and add it to the scene.

        Args:
            _eclass (EntityClass): EntityClass (INP or OUT), see custom/entity.py.
            _coords (QPointF): Scene-position of the terminal.
            _flag (bool, optional): Whether to push this action to the undo-stack (default: True).

        Returns:
            _terminal (StreamTerminal): Reference to the newly created terminal
        """
        # Type-check input args:
        if  not isinstance(_flag, bool):
            logging.info(f"Invalid arg-type: {type(_flag)}")
            return None

        if  _eclass not in [EntityClass.INP, EntityClass.OUT]:
            logging.info(f"Invalid arg-type: {type(_eclass)}")
            return None

        # If the input coordinate is `None`, use the cursor position:
        if _coords is None:   _coords = self._cpos

        # Debugging:
        logging.info(f"Creating new terminal at {_coords}")

        # Create a new terminal and position it:
        _terminal = StreamTerminal(_eclass, None)
        _terminal.setPos(_coords)
        _terminal.handle.sig_item_clicked.connect(self.begin_transient, Qt.ConnectionType.UniqueConnection)
        _terminal.handle.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED), Qt.ConnectionType.UniqueConnection)
        _terminal.sig_item_removed.connect(self.on_item_removed)

        # Add item to canvas:
        self.term_db[_terminal] = EntityState.ACTIVE
        self.addItem(_terminal)

        # If the flag is set, create the corresponding action and push it to the undo-stack:
        if _flag: self.manager.do(CreateStreamAction(self, _terminal))

        # Set state-variable:
        self.sig_canvas_state.emit(SaveState.MODIFIED)

        # Return terminal:
        return _terminal

    def create_cuid(self):
        """
        Returns a unique ID for a new connector. The ID is of the form "X" followed by the smallest integer not already used

        :return: str: Unique ID for a new connector.
        """

        # Get existing connector UIDs:
        id_set = {
            int(_connector.symbol.split('X')[1])
            for _connector, state in self.conn_db.items()
            if  state == EntityState.ACTIVE
        }

        # If `id_set` is empty, return "X0":
        if not id_set:  return "X0"
        
        # Get sequence of integers from 0 to `max(id_set) + 1`, not in `id_set`:
        sequence = set(range(0, max(id_set) + 2))
        reusable = sequence - id_set

        # Return UID (prefix + smallest integer not in `id_set`):
        return "X" + str(min(reusable))

    def create_nuid(self):
        """
        Create a unique ID for a new _node.
        """

        id_set = {
            int(_node.uid.split('N')[1])
            for _node, state in self.node_db.items()
            if state
        }

        # If `id_set` is empty, return "N0":
        if not id_set:  return "N0000"
        
        # Get sequence of integers from 0 to `max(id_set) + 1`, not in `id_set`:
        sequence = set(range(0, max(id_set) + 2))
        reusable = sequence - id_set

        # Return UID (prefix + smallest integer not in `id_set`):
        return "N" + str(min(reusable)).zfill(4)

    def store(self):
        """
        Add selected items to the clipboard.

        Returns:
            None
        """

        # If items have been selected:
        if  self.selectedItems():
            self.Registry.clipboard = self.selectedItems()  # Store reference(s)

        # Otherwise, beep (uses the default notification
        else: QApplication.beep()

    def clone(self):
        """
        Clone the clipboard's contents and add them to the canvas.

        Returns:
            None
        """
        # Create batch-commands:
        batch = BatchActions([])

        # Duplicate items:
        for item in Canvas.Registry.clipboard:

            # If the item is a node...:
            if  isinstance(item, Node):

                # Instantiate clone
                item_clone = item.clone(set_uid = self.create_nuid())

                # Add to canvas:
                self.node_db[item_clone] = EntityState.ACTIVE
                self.addItem(item_clone)

                # Add to batch-operations:
                batch.add_to_batch(CreateNodeAction(self, item_clone))

            # If the item is a terminal...:
            elif isinstance(item, StreamTerminal):

                # Instantiate clone
                item_clone = item.clone()

                # Add to canvas:
                self.term_db[item_clone] = EntityState.ACTIVE
                self.addItem(item_clone)

                # Add to batch operations:
                batch.add_to_batch(CreateStreamAction(self, item_clone))

        # Re-establish connections:
        while Handle.cmap:

            try:
                # `_handle` and `conjugate` belong to the copied nodes. `origin` and `target` are their mirrors in the
                # copied nodes that must now be connected:
                _handle   , origin = Handle.cmap.popitem()
                _conjugate, target = _handle.conjugate(), Handle.cmap[_handle.conjugate()]          # Throws exception if `_handle` is not connected

                # If an exception is not thrown, both origin and target are valid, connected handles:
                Handle.cmap.pop(_conjugate)  # Remove the key corresponding to _handle's conjugate

                # Create a new connector between the origin and target handles:
                # Then add it to the database and to the QGraphicsScene:
                _connector = Connector(self.create_cuid(), origin, target)
                _connector.sig_item_removed.connect(self.on_item_removed)

                # Add _connector to canvas:
                self.conn_db[_connector] = EntityState.ACTIVE
                self.addItem(_connector)

                # Add _connector-creation to batch:
                batch.add_to_batch(ConnectHandleAction(self, _connector))

            except KeyError as key_error:       # Thrown by `Handle.cmap`
                logging.error(f"KeyError: {key_error}")
                pass

            except TypeError as type_error:     # Thrown by `_handle`
                logging.error(f"TypeError: {type_error}")
                pass

        # Execute:
        if batch.size():    self.manager.do(batch)

    def paste_item(self, 
                  _item: QGraphicsObject,   # Item to be pasted.
                  _stack: bool = False      # Should the action be pushed to the undo-stack?
                  ):
        """
        Paste a _node or a terminal item onto the canvas.

        Args:
            _item (QGraphicsObject): The item to be pasted.
            _stack (bool):
        """

        # Find the item's type:
        if isinstance(_item, Node):
            _item.uid = self.create_nuid()
            _item.sig_item_removed.connect(self.on_item_removed)
            _item.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED))
            _item.sig_exec_actions.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED))
            _item.sig_exec_actions.connect(self.manager.do)
            _item.sig_handle_clicked.connect(self.begin_transient)
            self.node_db[_item] = EntityState.ACTIVE

        elif isinstance(_item, StreamTerminal):
            _item.handle.sig_item_clicked.connect(self.begin_transient)
            _item.handle.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.MODIFIED))
            _item.sig_item_removed.connect(self.on_item_removed)
            self.term_db[_item] = EntityState.ACTIVE

        # Add item to canvas:
        self.addItem(_item)

        # If `_stack` is True, create the corresponding action and forward it to the stack-manager:
        if _stack:
            # TODO: Push action to undo-stack
            pass

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.MODIFIED)

    def select_items(self, _items_dict: dict = None):
        """
        Select items in the canvas:
        """

        [
            item.setSelected(True)                  # Select all items
            for item, state in _items_dict.items()  # in the dictionary
            if  item in self.items() and state      # if they belong to the canvas and are visible/enabled
        ]

    def delete_items(self, _items: set | list):
        """
        Deletes items from the canvas using undoable batch-actions.

        Args:
            _items (set): Set of items (nodes and terminals) to delete.
        """

        # Create batch-commands:
        batch = BatchActions([])

        # Delete items in the dictionary:
        for item in _items:

            if  isinstance(item, Node) and self.node_db[item]:
                batch.add_to_batch(RemoveNodeAction(self, item))

            elif isinstance(item, StreamTerminal) and self.term_db[item]:
                batch.add_to_batch(RemoveStreamAction(self, item))
    
        # Execute batch:
        if batch.size():    self.manager.do(batch)

    def symbols(self):

        symlist = list()
        for _node, state in self.node_db.items():
            if  state == EntityState.ACTIVE:
                symlist += _node.symbols()

        for conn, state in self.conn_db.items():
            if  state == EntityState.ACTIVE:
                symlist.append(conn.symbol)

    # Method to import a JSON schematic:
    @pyqtSlot()
    @pyqtSlot(str)
    def import_schema(self, file: str | None = None):
        """
        Import a JSON schematic and populate the canvas with its contents.

        :param: file (str, optional): The path to the JSON file to be imported.
        """

        # Debugging:
        logging.info("Opening JSON file")

        # Get the file path if it hasn't been provided:
        if not isinstance(file, str):
            
            file, code = QFileDialog.getOpenFileName(None, "Select JSON file", "./", "JSON files (*.json)")
            if  not code:
                logging.info("Open operation cancelled!")
                return None

        # Open the file:
        with open(file, "r+") as json_str:
            code = json_str.read()
            
        # Decode JSON-string:
        json = JsonLib.decode(code, self, True)

        # Notify application of state-change:
        self.sig_schema_setup.emit(file)
        self.sig_canvas_state.emit(SaveState.MODIFIED)

        # Return the file-path:
        return file

    # Method to encode the schematic to a JSON string and save it to a file:
    @pyqtSlot()
    @pyqtSlot(str)
    def export_schema(self, _name: str = str()):
        """
        Export the canvas's contents (schematic) as a JSON file.

        :param: _name (str): The name of the file to export the schematic to.
        """

        # Get a new filename if `_export_name` is empty:
        _name, _ = QFileDialog.getSaveFileName(None,
                                               "Select save-file",
                                               ".", "JSON (*.json)"
                                               ) \
                   if   _name == str() or not isinstance(_name, str) \
                   else _name, True

        try:
            _json = JsonLib.encode(self)
            _file = open(_name, "w+")
            _file.write(_json)

            # Notify application of state-change:
            self.state = SaveState.EXPORTED
            self.sig_canvas_state.emit(self.state)

            # Return the file name to indicate success:
            return _name

        except Exception as exception:

            Dialog.warning(None,
                            "Climact: Save Failed",
                            f"Error saving to file. Please check log file for details.")

            logging.info(f"Exception caught: {exception}")  # Output to the log file
            self.sig_canvas_state.emit(SaveState.ERROR)     # Notify application of error state
            return None

    @pyqtSlot(Handle)
    def begin_transient(self, _handle: Handle):
        """
        Activate the transient-connector.

        Args:
            _handle (Handle): Emitter of the signal (tabs/schema/graph/handle.py).

        Returns: 
            None
        """

        # Abort-conditions:
        if (
            self._conn.active or                # If the transient-connector is already active.
            self._conn.origin or                # If the origin-handle is already connected.
            not isinstance(_handle, Handle)     # If the signal-emitter is not a Handle.
        ):
            return
        
        # Set transient-attributes:
        self._conn.active = True
        self._conn.origin = weakref.ref(_handle)

    @pyqtSlot()
    def reset_transient(self):
        """
        Reset the transient-connector, clear reference(s) to origin and target
        """

        # Reset transient-attributes:
        self._conn.active = False
        self._conn.origin = None
        self._conn.target = None
        self._conn.connector.clear()

    def on_item_removed(self):
        """
        This slot is triggered when the signal-emitter (QGraphicsObject) is deleted by the user. This method, however,
        hides the object and pushes an undoable action to the stack so that the object can be restored later using
        the undo/redo functionality.
        """

        # Get signal-emitter:
        item = self.sender()
       
        # Validate signal-emitter:
        if (
            isinstance(item, QGraphicsObject) and
            item.scene() == self
        ):
            self.delete_items({item: True})  # Delete item
    
    def find_stream(self, strid: str, create: bool = False):
        """
        Find a stream by its name. If the stream does not exist, create it (optional)
        :param strid: Name of the stream to find.
        :param create: If True, create the stream if it does not exist. Default is True.
        """

        strid  = strid.replace("<b>", "").replace("</b>", "").strip()
        stream = next((stream for stream in self.type_db if stream.strid == strid), None)

        # If the stream does not exist and `_create` is True, create it:
        if  stream is None and create:
            stream = Stream(strid, QColor(random_hex()))
            self.type_db.add(stream)

        # Return stream:
        return stream

    def find_node(self, _uid: str):

        for _node in self.node_db.keys():
            if self.node_db[_node] and _uid == _node.uid:
                return _node

        return None

    def clear(self):
        """
        Clears the canvas after user confirmation. This action cannot be undone.

        Returns:
            None
        """

        # Abort-conditions:
        if  len(self.items()) <= 1: # Less than 1 because the transient-connector must be discounted
            Dialog.information(None, "Info", "No items on the scene!")
            return

        # Initialize confirmation-dialog:
        message = Dialog(QtMsgType.QtWarningMsg,
                          "This action cannot be undone. Are you sure?",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                         )

        # If the user confirms, delete nodes and streams:
        if message.exec() == QMessageBox.StandardButton.Yes:
            self.delete_items(self.node_db) # Delete nodes
            self.delete_items(self.term_db) # Delete terminals

            # Safe-delete undo and redo stacks:
            self.manager.wipe_stack()

        # Note: Do not forward the event to super-class, this will delete the transient-connector and cause a crash!

    # ------------------------------------------------------------------------------------------------------------------
    # PROPERTIES
    # Name                    Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. uid                  The canvas's unique ID.
    # ------------------------------------------------------------------------------------------------------------------
    
    @property
    def uid(self)   -> str:  return self.objectName()

    # Unique ID setter:
    @uid.setter
    def uid(self, value: str):   self.setObjectName(value if isinstance(value, str) else self.uid)