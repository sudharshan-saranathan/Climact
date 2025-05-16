#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------
import logging
import weakref
from pathlib import Path

from PyQt6.QtGui  import QColor, QTransform
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

from dataclasses import dataclass
from .graph   import *
from .jsonlib import JsonLib

from util    import random_id
from enum    import Enum
from custom  import *
from actions import *

class SaveState(Enum):
    SAVED = 0
    UNSAVED = 1

# Class Canvas - Subclass of QGraphicsScene, manages graphical items:
class Canvas(QGraphicsScene):

    # Signals:
    sig_item_created = pyqtSignal()             # Emitted when a new item is created.
    sig_item_removed = pyqtSignal()             # Emitted when an item is removed.
    sig_canvas_reset = pyqtSignal()             # Emitted when the canvas is reset.
    sig_canvas_state = pyqtSignal(SaveState)    # Emitted when the canvas's state changes.
    sig_schema_setup  = pyqtSignal(str)          # Emitted when a JSON-schematic is loaded.

    # Placeholder-connector:
    class Transient:
        def __init__(self):
            self.active = False                 # Set to True when a connection is being drawn by the user, False otherwise.
            self.origin = None                  # Reference pointer to the connector's origin (tabs/schema/graph/handle.py).
            self.target = None                  # Reference pointer to the connector's target (tabs/schema/graph/handle.py).
            self.connector = Connector("")      # Connector object (tabs/schema/graph/connector.py).

    # Global registry:
    @dataclass
    class Registry:
        clipboard = list()

    # CANVAS (Initializers) --------------------------------------------------------------------------------------------
    # Instance initializer:
    def __init__(self, bounds: QRectF, parent: QObject | None = None):
        """
        Initialize the canvas with a given rectangular boundary and optional parent

        Parameters:
            rect (QRectF): The initial dimensions of the scene
            parent (QObject, optional): Optional parent QObject (default: None)
        """

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

        # Add transient-connector to scene:
        self.addItem(self._conn.connector)

        # Customize attribute(s):
        self.setSceneRect(bounds)
        self.setBackgroundBrush(QColor(0xefefef))
        self.setObjectName(random_id(length=4, prefix='S'))

        # Initialize registries:
        self.term_db = dict()  # Maps each terminal to a bool indicating whether it's currently visible/enabled.
        self.node_db = dict()  # Maps each node to a bool indicating whether it's currently visible/enabled.
        self.conn_db = dict()  # Maps each connector to a bool indicating whether it's currently visible/enabled.
        self.type_db = set()   # List of defined stream-types (e.g. Mass, Energy, Electricity, etc.)

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
        Initializes the context menu with node creation, import/export, and group/clear actions.

        Parameters: None
        Returns: None
        """

        # Create menu:
        self._menu = QMenu()
        self._subm = self._menu.addMenu("Create Object")

        # Submenu for creating node_items:
        _node = self._subm.addAction("Node")
        _tout = self._subm.addAction("Terminal (Out)")
        _tinp = self._subm.addAction("Terminal (Inp)")

        # Import and export actions:
        self._menu.addSeparator()
        _load = self._menu.addAction("Import Schema")
        _save = self._menu.addAction("Export Schema")

        # Group and Clear actions:
        self._menu.addSeparator()
        _group = self._menu.addAction("Group Items")
        _clear = self._menu.addAction("Clear Scene")

        self._menu.addSeparator()
        _exit = self._menu.addAction("Quit Application")

        # Connect actions to slots:
        _node.triggered.connect(lambda: self.create_node("Node"))
        _load.triggered.connect(lambda: self.import_schema())
        _save.triggered.connect(lambda: self.export_schema())
        _tinp.triggered.connect(lambda: self.create_terminal(EntityClass.INP, self._cpos))
        _tout.triggered.connect(lambda: self.create_terminal(EntityClass.OUT, self._cpos))
        _exit.triggered.connect(QApplication.quit)

        # Additional actions:
        _clear.triggered.connect(self.clear)

    # Event-Handlers ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. contextMenuEvent       Handles context-menu events (triggered when the user right-clicks on the canvas).
    # 2. mouseMoveEvent         If a connection is active, this event will continuously update the connector's path.
    # 3. mouseReleaseEvent      If a connection is active and the mouse-button was released at a target node's anchor, 
    #                           this event will create a new handle and establish a connection between the origin and 
    #                           target.
    # ------------------------------------------------------------------------------------------------------------------

    # Context-menu event handler:
    def contextMenuEvent(self, event):
        """
        Handle context-menu events, triggered by right-clicks.

        Parameters:
            event (QGraphicsSceneContextMenuEvent): Event instance, internally propagated by Qt.

        Returns: None
        """

        # Call super-class implementation first:
        super().contextMenuEvent(event)
        if event.isAccepted() or self._menu is None:    return

        # 1. Store scene-position (do not remove).
        # 2. Open menu at cursor position:
        self._cpos = event.scenePos()
        self._menu.exec(event.screenPos())
        event.accept()

    def mouseMoveEvent(self, event):
        """
        Handle mouse-move events. When a connection is active, this handler will continuously update the connector's path
        as the cursor is dragged across the scene.

        Parameters:
            event (QGraphicsSceneMouseEvent): Event instance, internally propagated by Qt.

        Returns: None
        """

        # Forward event to other handlers:
        super().mouseMoveEvent(event)

        # If transient-connector is active, update its path:
        if  self._conn.active:
            self._conn.connector.draw(self._conn.origin().scenePos(), 
                                      event.scenePos(), 
                                      PathGeometry.BEZIER
                                      )

    def mouseReleaseEvent(self, event):
        """
        Handle mouse-release events.

        Parameters:
            event (QGraphicsSceneMouseEvent): Event instance, internally propagated by Qt.

        Returns: None
        """
    
        # If transient-connector is inactive, or the release event is not a left-click, forward event to super-class:
        if (
            not self._conn.active or 
            event.button() != Qt.MouseButton.LeftButton
        ):
            # Forward event to super-class and return:
            super().mouseReleaseEvent(event)
            return

        # Define convenience variables:
        _tpos = event.scenePos()                    # Release-position in scene-coordinates.
        _node = self._conn.origin().parentItem()    # Origin handle's parent item (could be a node or a terminal).

        # Find item below the cursor:
        _item = self.itemAt(event.scenePos(), QTransform())

        # If the item below the cursor is an anchor, create a new handle at the target anchor:
        if isinstance(_item, Anchor):

            # Verify that the target anchor's parent node is different from the origin handle's parent node:
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
        _origin = self._conn.origin()               # Origin handle is set in `self.begin_transient()`
        _target = self.itemAt(_tpos, QTransform())  # This should return the new handle created at the target anchor.

        # Abort-conditions:
        if (
            not isinstance(_target, Handle) or
            _target.connected or
            _origin == _target or
            _origin.eclass == _target.eclass or
            _origin.parentItem() == _target.parentItem()
        ):
            self.reset_transient()
            super().mouseReleaseEvent(event)
            return

        # Create new connection between origin and target, and add it to the canvas:
        _connector = Connector(self.create_cuid(), _origin, _target)
        self.conn_db[_connector] = True
        self.addItem(_connector)

        # Push action to undo-stack:
        self.manager.do(ConnectHandleAction(self, _connector))

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.UNSAVED)

        # Reset transient-connector:
        self.reset_transient()

        # Forward event to super-class:
        super().mouseReleaseEvent(event)

    # Custom Methods ---------------------------------------------------------------------------------------------------
    # Name                      Description
    # ------------------------------------------------------------------------------------------------------------------
    # 1. create_terminal        Creates a new source or sink terminal with a single connection point.
    # 2. create_node            Creates a new node with a single connection point.
    # 3. create_cuid            Creates a unique ID for a new connector.
    # 4. import_schema          Reads a JSON-schematic and populates the canvas with the schematic's contents.
    # 5. export_schema          Saves the canvas's contents as a JSON-schematic.
    # ------------------------------------------------------------------------------------------------------------------

    def create_terminal(self,
                      _eclass : EntityClass,  # EntityClass (INP or OUT), see custom/entity.py.
                      _coords : QPointF,       # Position of the terminal (in scene-coordinates).
                      _flag   : bool = True    # Should the action be pushed to the undo-stack?
                      ):             


        """
        Create a new terminal with a single connection point.

        Parameters:
            _eclass (EntityClass): EntityClass (INP or OUT), see custom/entity.py.
            _coords (QPointF): Scene-position of the terminal.
            _flag (bool, optional): Whether to push this action to the undo-stack (default: True).

        Returns: None
        """

        # Validate argument(s):
        if not isinstance(_flag, bool): return
       
        # Validate _class:
        if _eclass not in [EntityClass.INP, EntityClass.OUT]:
            raise ValueError("Invalid entity class")
        
        # Debugging:
        logging.info(f"Creating new terminal at {_coords}")

        # Create new terminal and position it:
        _terminal = StreamTerminal(_eclass, None)
        _terminal.setPos(_coords)
        _terminal.socket.sig_item_clicked.connect(self.begin_transient, Qt.ConnectionType.UniqueConnection)
        _terminal.socket.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED), Qt.ConnectionType.UniqueConnection)
        _terminal.sig_item_removed.connect(self.on_item_removed)

        # Add item to canvas:
        self.term_db[_terminal] = True
        self.addItem(_terminal)

        # If flag is set, create and forward action to stack-manager:
        if _flag: self.manager.do(CreateStreamAction(self, _terminal))

        # Set state-variable:
        self.sig_canvas_state.emit(SaveState.UNSAVED)

        # Return terminal:
        return _terminal

    def create_node(self, 
                   _name: str = "Node", 
                   _cpos: QPointF | None = None,
                   _push: bool = True
                   ):
        """
        Create a new node at the specified scene-position

        Args:
            _name (str, optional): The name of the node (default: "Node").
            _cpos (QPointF, optional): The position of the node (in scene-coordinates).
            _push (bool): Flag that determines whether the action will be pushed to the stack.

        Returns: 
            Node: The newly created node.
        """

        # Set coordinate(s):
        _cpos = self._cpos if _cpos is None else _cpos

        # Create new node and position it:
        _node = Node(_name, _cpos, None)
        _node.uid = self.create_nuid()

        # Connect node's signal(s) to appropriate slots:
        _node.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED))
        _node.sig_exec_actions.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED))
        _node.sig_exec_actions.connect(self.manager.do)
        _node.sig_item_removed.connect(self.on_item_removed)
        _node.sig_handle_clicked.connect(self.begin_transient)

        # Add node to database and canvas:
        self.node_db[_node] = True
        self.addItem(_node)

        # Push action to undo-stack:
        if _push:   self.manager.do(CreateNodeAction(self, _node))

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.UNSAVED)

        # Return reference to newly created node:
        return _node

    def create_cuid(self):
        """
        Create a unique ID for a new connector.

        Parameters: None
        Returns: 
            str: Unique ID for a new connector.
        """

        # Get existing connector UIDs:
        id_set = {
            int(connector.symbol.split('X')[1])
            for connector in self.conn_db
            if self.conn_db[connector]
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
        Create a unique ID for a new node.
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

    def copy_selection(self):
        """
        Copy the currently selected item(s) to the clipboard.

        Parameters: None
        Returns: None
        """

        # Copy selected items to clipboard:
        Canvas.Registry.clipboard = self.selectedItems()

        # Debugging:
        logging.info("Selected items copied to clipboard")

    def paste_selection(self):
        """
        Paste the clipboard's contents onto the canvas.

        Parameters: None
        Returns: None
        """
        # Create batch-commands:
        batch = BatchActions([])

        # Duplicate items:
        for item in Canvas.Registry.clipboard:
            
            # Duplicate item (node or terminal):
            _copy = item.duplicate(self)

            # Add to batch-action:
            if      isinstance(item, Node)          : batch.add_to_batch(CreateNodeAction(self, _copy))
            elif    isinstance(item, StreamTerminal): batch.add_to_batch(CreateStreamAction(self, _copy))

            # Add copy to node-database so that `create_nuid()` returns a unique ID:
            if   isinstance(item, Node)          : self.node_db[_copy] = True
            elif isinstance(item, StreamTerminal): self.term_db[_copy] = True

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
                connector = Connector(self.create_cuid(), origin, target)
                connector.sig_item_removed.connect(self.on_item_removed)

                # Add connector to canvas:
                self.conn_db[connector] = True
                self.addItem(connector)

                # Add connector-creation to batch:
                batch.add_to_batch(ConnectHandleAction(self, connector))

            except KeyError as key_error:       # Thrown by `Handle.cmap`
                logging.error(f"KeyError: {key_error}")
                pass

            except TypeError as type_error:     # Thrown by `handle`
                logging.error(f"TypeError: {type_error}")
                pass

        # Execute:
        if batch.size():    self.manager.do(batch)

    def paste_item(self, 
                  _item: QGraphicsObject,   # Item to be pasted.
                  _stack: bool = False      # Should the action be pushed to the undo-stack?
                  ):
        """
        Paste an item onto the canvas.

        Parameters:
            _item (QGraphicsObject): The item to be pasted.
            _stack (bool):
        """

        # Find type of item:
        if isinstance(_item, Node):
            _item.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED), Qt.ConnectionType.UniqueConnection)
            _item.sig_exec_actions.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED), Qt.ConnectionType.UniqueConnection)
            _item.sig_exec_actions.connect(self.manager.do, Qt.ConnectionType.UniqueConnection)
            _item.sig_item_removed.connect(self.on_item_removed, Qt.ConnectionType.UniqueConnection)
            _item.sig_handle_clicked.connect(self.begin_transient, Qt.ConnectionType.UniqueConnection)
            _item.uid = self.create_nuid()

        elif isinstance(_item, StreamTerminal):
            self.term_db[_item] = True
            _item.socket.sig_item_clicked.connect(self.begin_transient)
            _item.socket.sig_item_updated.connect(lambda: self.sig_canvas_state.emit(SaveState.UNSAVED))
            _item.sig_item_removed.connect(self.on_item_removed)

        # Add item to canvas:
        self.addItem(_item)

        # If `_stack` is True, create and forward action to stack-manager:
        if _stack:
            # TODO: Push action to undo-stack
            pass

        # Notify application of state-change:
        self.sig_canvas_state.emit(SaveState.UNSAVED)

    def select_items(self, _items_dict: dict):
        """
        Select the items in the set.
        """

        [
            item.setSelected(True)
            for item, state in _items_dict.items()
            if state
        ]

    def delete_items(self, _items: dict):
        """
        Deletes items from the canvas using undoable batch-actions.

        Parameters:
            _items (set): Set of items (nodes & terminals) to delete.

        Returns: None
        """

        print(f"Deleting: {_items}")

        # Create batch-commands:
        batch = BatchActions([])

        # Delete items in the dictionary:
        for item in _items:

            if isinstance(item, Node) and self.node_db[item]:
                batch.add_to_batch(RemoveNodeAction(self, item))

            elif isinstance(item, StreamTerminal) and self.term_db[item]:
                batch.add_to_batch(RemoveStreamAction(self, item))
    
        # Execute batch:
        if batch.size():    self.manager.do(batch)

    def symbols(self):

        _symbols = list()
        for _node, _state in self.node_db.items():
            if _state:
                _symbols += _node.symbols()

        for _conn, _state in self.conn_db.items():
            if _state:
                _symbols.append(_conn.symbol)

    @pyqtSlot(str)  # Method to import a JSON-schematic
    def import_schema(self, _file: str | None = None):
        """
        Import a JSON-schematic from a file.

        Parameters:
            _file (str, optional): The path to the JSON-file to be imported.

        Returns: None
        """

        # Debugging:
        logging.info("Opening JSON file")

        # Get file-path if it hasn't been provided:
        if not isinstance(_file, str):
            
            _file, _code = QFileDialog.getOpenFileName(None, "Select JSON file", "./", "JSON files (*.json)")
            if not _code: 
                logging.info("Open operation cancelled!")
                return

        # Open file:
        with open(_file, "r+") as _json_str:
            _code = _json_str.read()
            
        # Decode JSON-string:
        _json = JsonLib.decode_json(_code, self, _group_actions=True)

        # Notify application of state-change:
        # self.sig_json_loaded.emit (Path(_file).name )
        self.sig_canvas_state.emit(SaveState.UNSAVED)

    @pyqtSlot(str)  # Method to export a JSON-schematic 
    def export_schema(self, _export_name: str | None = None):
        """
        Export the canvas's contents (schematic) as a JSON-file.

        Args:
            _export_name (str): The name of the file to export the schematic to.

        Returns: None
        """

        # Try-block:
        try:
            
            # Encode canvas' contents to JSON-string, then write to file:
            _json_str = JsonLib.encode_json(self)
            with open(_export_name, "w+") as _file:
                _file.write(_json_str)

            # Notify application of state-change:
            self.sig_canvas_state.emit(SaveState.SAVED)

        # Exception chain:
        except Exception as exception:
            
            # Instantiate error-dialog:
            _error_dialog = Dialog(QtMsgType.QtCriticalMsg, exception, QMessageBox.StandardButton.Ok)
            _error_dialog.exec()
            
            logging.error(f"Error encoding JSON: {exception}")
            return

    @pyqtSlot(Handle)
    def begin_transient(self, _handle: Handle):
        """
        Activate the transient-connector.

        Parameters:
            _handle (Handle): Emitter of the signal (tabs/schema/graph/handle.py).

        Returns: None
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
        Reset transient-connector's path, clear reference(s) to origin and target

        Parameters: None
        Returns: None
        """

        # Reset transient-attributes:
        self._conn.active = False
        self._conn.origin = None
        self._conn.target = None
        self._conn.connector.clear()

    def on_item_removed(self):
        """
        Slot triggered when an emits a 'sig_item_removed' signal. Deletes the node.
        """

        # Get signal-emitter:
        item = self.sender()
       
        # Validate signal-emitter:
        if (
            isinstance(item, QGraphicsObject) and
            item.scene() == self
        ):
            self.delete_items({item: True})  # Delete item
    
    def find_stream(self, _stream: str):
        """
        Find a stream by its name.

        Args:
            _stream (str): The name of the stream to find.

        Returns:
            Stream: The stream with the given name (see custom/stream.py).
        """

        return next((stream for stream in self.type_db if stream.strid == _stream), None) 

    def find_node(self, _uid: str):

        for _node in self.node_db.keys():
            if self.node_db[_node] and _uid == _node.uid:
                return _node

        return None

    def clear(self):
        """
        Clears the canvas after user confirmation. This action cannot be undone.
        
        Parameters: None
        Returns: None
        """

        # Abort-conditions:
        if  len(self.items()) <= 1: # Less than 1 because the transient-connector must be discounted
            message = Dialog(QtMsgType.QtInfoMsg, "No items in the scene!")
            message.exec()
            return

        # Initialize confirmation-dialog:
        dialog = Dialog(QtMsgType.QtWarningMsg,
                        "This action cannot be undone. Are you sure?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
                        )

        # If user confirms, delete nodes and streams:
        if dialog.exec() == QMessageBox.StandardButton.Yes:

            # Delete nodes and terminals:
            self.delete_items(self.node_db)
            self.delete_items(self.term_db)

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

    @property
    def state(self) -> SaveState:
        """
        Get the state of the canvas.
        """
        return SaveState.UNSAVED
