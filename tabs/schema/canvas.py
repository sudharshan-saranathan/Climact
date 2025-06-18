"""
canvas.py
---------
This module is part of the Climact application. It defines a custom class `Viewer` (subclass of `QGraphicsView`, see Qt
documentation for more details) for displaying and interacting with graphical content.
"""

__author__  = "Sudharshan Saranathan"
__version__ = "0.1.0"
__license__ = "None"
__date__    = "2025-05-26"

# Imports:
import types                # Standard library module for creating variables with dynamic attributes
import logging              # Standard library module for logging
import dataclasses          # Standard library module for creating classes with automatic attribute management
import weakref
from pathlib import Path

import qtawesome as qta     # Qtawesome for creating icons and other UI elements

from PyQt6.QtCore import (
    QRectF,
    QPointF,
    QObject, pyqtSlot, pyqtSignal, Qt
)
from PyQt6.QtGui import (
    QTransform,
    QKeySequence, QColor, QAction
)
from PyQt6.QtWidgets import (
    QMenu,
    QGraphicsScene,
    QGraphicsPathItem, QGraphicsItem, QGraphicsObject
)

from actions import *
from custom import EntityState, EntityRole, Getter

from enum   import Enum
from util import ValidatorDict, validator, random_id  # Custom utility for creating typed dictionaries

# Graphics Objects:
from .graph.node      import Node
from .graph.anchor    import Anchor
from .graph.handle    import Handle
from .graph.connector import Connector
from .graph.terminal import StreamTerminal
from .jsonio import JsonIO


@dataclasses.dataclass(frozen=True, eq=True)
class CanvasState(Enum):
    """
    An enumeration to represent the save state of the canvas.
    """
    UNSAVED = 0  # The canvas has unsaved changes
    SAVED = 1    # The canvas is saved
    ERROR = 2    # There was an error saving the canvas
    LOADED = 3   # The canvas has been loaded from a file

@dataclasses.dataclass(frozen=True, eq=True)
class CanvasItems(Enum):
    """
    An enumeration to represent the types of items to select.
    """
    ALL  = 0            # Represents all items
    NODE = 1            # Represents nodes
    TERMINAL = 2        # Represents terminals

# Class Canvas:
class Canvas(QGraphicsScene):
    """
    A subclass of `QGraphicsScene` for schematic-building.

    The `Canvas' class
    or graphs by interacting with various components like nodes, terminals, and connections. This cla
    This class supports context menus for graphical manipulation, undo/redo operations, and adding or removing
    graphical elements dynamically. Additionally, it manages the state of the canvas and offers clipboard
    support for cross-instance copy-paste operations.

    The core functionalities include signal handling for dynamic events, a stack-manager for undo/redo, and
    databases to organize, validate, and categorize graphical elements. It facilitates integration support for
    each component type while providing default visual attributes for an intuitive user experience.
    """

    # Signals:
    sig_canvas_changed = pyqtSignal(CanvasState)        # Signal emitted when the canvas changes.
    sig_loaded_project = pyqtSignal(str)                # Signal emitted when a project is loaded.
    sig_open_database  = pyqtSignal()                   # Signal to open the node's database-page.

    # Class-level clipboard to enable copy-pasting items, even across different Canvas instances:
    clipboard = dict()

    # Class Constructor:
    def __init__(self,
                 xsize: int,
                 ysize: int,
                 parent: QObject | None = None):

        # Initialize base-class constructor, customize attributes:
        super().__init__(QRectF(0, 0, xsize, ysize), parent)
        super().setObjectName(random_id(prefix='S'))            # Set a random ID for the canvas
        super().setBackgroundBrush(0xefefef)                    # Background color of the canvas (light gray)

        # Initialize stack-manager:
        self.manager = ActionsManager()

        # Additional attributes:
        self._attr = types.SimpleNamespace(
            cpos = QPointF(),               # Last context-menu position
            rect = self.sceneRect(),        # Bounding rectangle of the canvas
            stat = CanvasState.UNSAVED,     # Save-state of the canvas (default: UNSAVED)
        )

        # Instantiate transient connection and add it to the scene:
        self._transient = types.SimpleNamespace(
            active = False,                 # Set to `True` when a transient connection is active. The flag is checked by multiple methods.
            origin = None,                  # Origin of the transient connector (weak reference to a `Handle` object)
            object = Connector()            # `Connector` object (see tabs/schema/graph/connector.py for details)
        )
        self.addItem(self._transient.object)

        # Create a database for each item type:
        self.db = types.SimpleNamespace(
            node = ValidatorDict(Node),             # Typed dictionary for nodes
            conn = ValidatorDict(Connector),        # Database for connections
            term = ValidatorDict(StreamTerminal),   # Database for terminals
            kind = ValidatorDict(str)               # Database for entity-streams
        )

        # Add default streams:
        self.db.kind["Default"] = QColor(Qt.GlobalColor.lightGray)  # Default stream color
        self.db.kind["Energy"] = QColor(0xF6AE2D)                   # Energy stream color
        self.db.kind["Power"] = QColor(0x474973)                    # Power stream color
        self.db.kind["Mass"] = QColor(0x028CB6)                     # Mass stream color

        # Initialize a context-menu:
        self._init_menu()

    def _init_menu(self):
        """
        Initializes the context menu for the canvas. This handler is called when the user right-clicks on the canvas.
        Actions displayed include copy, paste, undo, redo, and delete.
        """

        self._menu = QMenu()                                    # Create a new menu
        self._subm = self._menu.addMenu("Create")               # Submenu

        node_action = self._subm.addAction(
            qta.icon('ri.node-tree', color='black'), "Node",
            QKeySequence("Ctrl+N"),
            self.create_node
        )

        tinp_action = self._subm.addAction(
            qta.icon("ph.sign-out", color='black'),
            "Terminal (Inp)", QKeySequence("Ctrl+["),
            lambda: self.create_term(EntityRole.INP)
        )

        tout_action = self._subm.addAction(
            qta.icon("ph.sign-in", color='black'),
            "Terminal (Out)", QKeySequence("Ctrl+]"),
            lambda: self.create_term(EntityRole.OUT)
        )

        self._menu.addSeparator()

        open_action = self._menu.addAction(
            qta.icon('fa6s.file', color='teal'),
            "Import Schema", QKeySequence.StandardKey.Open,
            self.import_project
        )

        save_action = self._menu.addAction(
            qta.icon('fa6s.floppy-disk', color='darkgreen'),
            "Export Schema", QKeySequence.StandardKey.Save,
            self.export_project
        )
        self._menu.addSeparator()

        undo_action = self._menu.addAction(
            qta.icon('ph.arrow-u-up-left', color='black'),
            "Undo", QKeySequence.StandardKey.Undo
        )

        redo_action = self._menu.addAction(
            qta.icon('ph.arrow-u-up-right', color='black'),
            "Redo" , QKeySequence.StandardKey.Redo
        )

        clone_action = self._menu.addAction(
            qta.icon('mdi.content-copy', color='purple'),
            "Clone", QKeySequence.StandardKey.Copy
        )

        paste_action = self._menu.addAction(
            qta.icon('mdi.content-paste', color='orange'),
            "Paste", QKeySequence.StandardKey.Paste
        )
        self._menu.addSeparator()

        select_action = self._menu.addAction(
            qta.icon('ph.selection-all', color='black'),
            "Select All", QKeySequence.StandardKey.SelectAll,
            self.select_all
        )

        delete_action = self._menu.addAction(
            qta.icon('ph.trash', color='darkred'),
            "Delete Items", QKeySequence.StandardKey.Delete,
            lambda: self.delete_items(self.selectedItems())
        )
        self._menu.addSeparator()

        find_action = self._menu.addAction(
            qta.icon('mdi.magnify', color='black'),
            "Find Item", QKeySequence.StandardKey.Find
        )

        group_action = self._menu.addAction(
            qta.icon('mdi.group', color='black'),
            "Group Items", QKeySequence("Ctrl+G")
        )

        clear_action = self._menu.addAction(
            qta.icon('mdi.eraser', color='red'),
            "Clear Canvas", QKeySequence("Ctrl+Shift+C"),
            self.clear_scene
        )
        self._menu.addSeparator()

        rearrange_action = self._menu.addAction("Rearrange", self.rearrange)

        exit_action = self._menu.addAction(
            qta.icon('ph.sign-out', color='magenta'),
            "Quit", QKeySequence.StandardKey.Quit
        )

        # Make icons visible:
        node_action.setIconVisibleInMenu(True)
        tinp_action.setIconVisibleInMenu(True)
        tout_action.setIconVisibleInMenu(True)
        open_action.setIconVisibleInMenu(True)
        save_action.setIconVisibleInMenu(True)
        undo_action.setIconVisibleInMenu(True)
        redo_action.setIconVisibleInMenu(True)
        find_action.setIconVisibleInMenu(True)
        exit_action.setIconVisibleInMenu(True)
        clone_action.setIconVisibleInMenu(True)
        paste_action.setIconVisibleInMenu(True)
        group_action.setIconVisibleInMenu(True)
        clear_action.setIconVisibleInMenu(True)
        select_action.setIconVisibleInMenu(True)
        delete_action.setIconVisibleInMenu(True)

        # Make shortcuts visible:
        open_action.setShortcutVisibleInContextMenu(True)
        node_action.setShortcutVisibleInContextMenu(True)
        tinp_action.setShortcutVisibleInContextMenu(True)
        tout_action.setShortcutVisibleInContextMenu(True)
        save_action.setShortcutVisibleInContextMenu(True)
        undo_action.setShortcutVisibleInContextMenu(True)
        redo_action.setShortcutVisibleInContextMenu(True)
        find_action.setShortcutVisibleInContextMenu(True)
        exit_action.setShortcutVisibleInContextMenu(True)
        clone_action.setShortcutVisibleInContextMenu(True)
        paste_action.setShortcutVisibleInContextMenu(True)
        group_action.setShortcutVisibleInContextMenu(True)
        clear_action.setShortcutVisibleInContextMenu(True)
        select_action.setShortcutVisibleInContextMenu(True)
        delete_action.setShortcutVisibleInContextMenu(True)

    def _connect_node_signals(self, node: Node):
        """
        Connects the signals of a Node object to the appropriate event handlers in the Canvas.
        :param node:
        """
        # Connect the node's signals to event-handlers:
        node.sig_handle_clicked.connect(self.start_transient)  # When a handle is clicked, start a transient connection
        node.sig_item_removed.connect(self.on_item_removed)  # When the node is clicked, reset the transient connection
        node.sig_item_updated.connect(lambda: self.sig_canvas_changed.emit(CanvasState.UNSAVED))
        node.sig_item_clicked.connect(self.sig_open_database.emit)
        node.sig_exec_actions.connect(self.manager.do)

    def _connect_term_signals(self, term: StreamTerminal):
        """
        Connects the signals of a Node object to the appropriate event handlers in the Canvas.
        :param term: The StreamTerminal object whose signals are to be connected.
        """
        # Connect the terminal's signals to event-handlers:
        term.sig_handle_clicked.connect(self.start_transient)  # When a handle is clicked, start a transient connection
        term.sig_handle_updated.connect(lambda: self.sig_canvas_changed.emit(CanvasState.UNSAVED))
        term.sig_item_removed.connect(self.on_item_removed)     # When the terminal is clicked, reset the transient connection

    # ------------------------------------------------------------------------------------------------------------------
    # QGraphicsScene Event Handlers (Overridden methods):
    #
    # - contextMenuEvent    : Handles right-click context menu events on the canvas.
    # - mouseMoveEvent      : Responsible for updating the transient connection as the mouse moves.
    # - mouseReleaseEvent   : Responsible for creating new connections when the mouse is released.
    # ------------------------------------------------------------------------------------------------------------------

    def contextMenuEvent(self, event):
        """
        Handles right-click context menu events on the canvas. Displays the context menu at the position of the mouse
        click.
        """
        # Reset transient connection, because triggering the context menu while drawing a transient
        # will cause the transient to remain active even when no mouse buttons are pressed:
        self.reset_transient()

        # Forward the event to the super-class to handle context menu events:
        super().contextMenuEvent(event)     # Forward event to scene-items first
        if  event.isAccepted():             # If the event is handled, skip further processing
            return

        self._attr.cpos = event.scenePos()  # Update the context menu position to the mouse position
        self._menu.exec(event.screenPos())  # Display the context menu at the mouse position
        event.accept()                      # Accept the event to prevent further processing

    def mouseMoveEvent(self, event):
        """
        Updates the transient connector as the mouse moves (as long as the left mouse button is pressed).
        :param event:
        """
        # Forward the event to the super-class:
        super().mouseMoveEvent(event)

        # If a connection started by the user, update the connector according to the mouse-position:
        if (
            self._transient.active and      # If the user started a connection
            self._transient.origin          # If the origin handle is still valid
        ):
            self._transient.object.render(self._transient.origin().scenePos(), event.scenePos())
            self._transient.object.update()

    def mouseReleaseEvent(self, event):
        """
        If a transient connection is active, this method creates a new connection between nodes.
        :param event: The mouse release event.
        """
        # If no transient connection is active, forward the event to the super-class:
        if not self._transient.active:
            super().mouseReleaseEvent(event)
            return

        # Otherwise, begin a sequence of checks to see if a new connection should be created:
        # 1. First, get the item below the cursor:
        tpos = event.scenePos()                     # Get the position of the mouse release event in scene-coordinates
        item = self.itemAt(tpos, QTransform())      # Get the item at the mouse position

        # 2. If it's an anchor (of a different node), create a new handle:
        if (
            isinstance(item, Anchor) and
            item.parentItem() != self._transient.origin().parentItem() and
            item.role != self._transient.origin().role
        ):
            apos = item.mapFromScene(tpos)                      # Map to the anchor's coordinate system.
            item.sig_item_clicked.emit(QPointF(0, apos.y()))    # Simulate click to create a new handle.

        # 3. Check for the item under the cursor again:
        item = self.itemAt(tpos, QTransform())
        if (
            isinstance(item, Handle) and
            not item.connected and
            item != self._transient.origin()
        ):

            # Re-define origin and target based on their EntityRole (Origin = OUT, target = INP)
            origin = self._transient.origin()
            target = origin if origin.role == EntityRole.INP else item
            origin = origin if origin.role == EntityRole.OUT else item

            # Create a new connector with the origin and target handles:
            connector = Connector(self.create_cuid(), origin, target)

            # Add the connector to the canvas' database:
            self.addItem(connector)
            self.db.conn[connector] = EntityState.ACTIVE

            # Push the action to the stack:
            self.manager.do(ConnectHandleAction(self, connector))

        # Reset the transient connection:
        self.reset_transient()

        # Forward event to the super-class:
        super().mouseReleaseEvent(event)  # Forward the event to the super-class
        event.accept()

    # ------------------------------------------------------------------------------------------------------------------
    # User-defined methods:
    #
    # ------------------------------------------------------------------------------------------------------------------

    def create_nuid(self):
        """
        Creates a new unique identifier
        :return: A unique identifier as a string.
        """
        # Get the set of currently active node IDs:
        active_ids = set(
            int(node.uid.lstrip('N'))
            for node, state in self.db.node.items()
            if  state == EntityState.ACTIVE
        )

        index = 0
        while index in active_ids:
            index += 1

        return f"N{index:04d}"  # Return the new unique identifier as a string

    def create_cuid(self):
        """
        Creates a new unique identifier
        :return: A unique identifier as a string.
        """
        # Get the set of currently active node IDs:
        active_ids = set(
            int(conn.symbol.lstrip('X'))
            for conn, state in self.db.conn.items()
            if  state == EntityState.ACTIVE
        )

        index = 0
        while index in active_ids:
            index += 1

        return f"X{index}"

    @validator
    def create_node(self, cpos: QPointF | None = None, undoable: bool = True) -> Node:
        """
        Creates a new node with a unique identifier and adds it to the scene and database.

        This function creates a `Node` object with a unique identifier (`nuid`), a default name ("Node"), and sets the
        node's scene-position based on the provided `cpos` or the last-stored context-menu position. Optionally, the
        `undoable` flag can be set to `True` to make this operation undoable (by pushing it to the undo/redo stack).

        :param cpos: The position of the node in the scene. If None, `self._attr.cpos` is used as the default position.
        :param undoable: Indicates whether the operation should be made undoable. Defaults to True.
        :return: Reference to the newly created node.
        :rtype: Node
        """

        # Create a new node with a unique identifier:
        nuid = self.create_nuid()
        node = Node(nuid, "Node", cpos or self._attr.cpos)

        # TODO: Connect the node's signals to event-handlers:
        self._connect_node_signals(node)

        # Add the node to the scene and database:
        self.addItem(node)                          # Add the node to the scene
        self.db.node[node] = EntityState.ACTIVE     # Add the node to the database with an active state

        # If this method is triggered by a QAction, push the create-node action to the undo/stack:
        if  undoable:
            self.manager.do(CreateNodeAction(self, node))

        # Return reference to the newly created node:
        return node

    @validator
    def create_term(self, role: EntityRole, cpos: QPointF | None = None) -> StreamTerminal:
        """
        Creates a new stream terminal at the specified position or at the center of the canvas if no position is provided.
        :param role:
        :param cpos:
        :return:
        """

        terminal = StreamTerminal(role)                 # Create a new terminal with the specified role
        terminal.setPos(cpos or self._attr.cpos)        # Set the position of the terminal

        # Add the terminal to the scene and database:
        self.addItem(terminal)                          # Add the terminal to the scene
        self.db.term[terminal] = EntityState.ACTIVE     # Add the terminal to the database with an active state

        # Connect the terminal's signals to event-handlers:
        self._connect_term_signals(terminal)

        # Return reference to the newly created terminal:
        return terminal

    @validator
    def start_transient(self, handle: Handle):
        """
        This event-handler is called when the user clicks on a node's handle.
        """
        if self._transient.active:  return              # If a transient connection is already active, do nothing.

        self._transient.active = True                   # Set `active` to True.
        self._transient.origin = weakref.ref(handle)    # Store a weak-reference to the handle

    def reset_transient(self):
        """
        Resets the transient connection state.
        """
        self._transient.active = False      # Reset the transient connection state
        self._transient.origin = None       # Reset the origin handle reference
        self._transient.object.reset()      # Reset the transient connector's path

    def clear_scene(self):
        """
        Clears the canvas by removing all items from the scene and resetting the database.
        """


    def clone_items(self):
        """
        Clones the selected items in the canvas and adds them to the clipboard.
        """
        # Copy the selected items to the clipboard:
        Canvas.clipboard = self.selectedItems()

    def paste_items(self):
        """
        Pastes the items from the clipboard into the canvas at the current context menu position.
        """
        # Check if the clipboard is empty:
        if  not Canvas.clipboard:
            logging.info("Clipboard is empty. Nothing to paste!")
            return

        # Create batch actions:
        batch = BatchActions([])

        # Clone all items and paste them sequentially:
        for item in self.clipboard:

            # Skip items that are not of type Node or StreamTerminal:
            if  not isinstance(item, (Node, StreamTerminal)):
                continue

            # Create a clone of the item and set its position:
            clone = item.clone()                                # Clone the item
            clone.setPos(item.scenePos() + QPointF(25, 25))     # Stagger the clone by 25 pixels
            clone.setSelected(True)                             # Select the pasted item

            # Add item to the scene:
            self.addItem(clone)

            if isinstance(item, Node):
                clone.uid = self.create_nuid()
                self.db.node[clone] = EntityState.ACTIVE
                self._connect_node_signals(clone)
                batch.add_to_batch(CreateNodeAction(self, clone))

            if isinstance(item, StreamTerminal):
                self.db.term[clone] = EntityState.ACTIVE
                self._connect_term_signals(clone)
                batch.add_to_batch(CreateStreamAction(self, clone))

            # Unselect the original item:
            item.setSelected(False)

        # Re-establish connections:
        while Handle.clone_map:

            # From `Handle.clone_map`, get key-value pairs: key is the origin handle while value is the cloned handle.
            #
            origin   , cloned = Handle.clone_map.popitem()
            conjugate, target = origin.conjugate, Handle.clone_map.get(origin.conjugate, None)

            # Also, remove the handle's conjugate from the clone map (prevents double-counting):
            Handle.clone_map.pop(conjugate, None)

            # Create a new connector between the origin and target handles:
            if cloned and target:
                connector = Connector(self.create_cuid(), cloned, target)
                self.addItem(connector)
                self.db.conn[connector] = EntityState.ACTIVE

                batch.add_to_batch(ConnectHandleAction(self, connector))

        # Notify the application that the canvas has changed:
        self.manager.do(batch)  # Execute the batch operation
        self.sig_canvas_changed.emit(CanvasState.UNSAVED)

    def select_all(self):
        """
        Selects all items in the canvas.
        """

        for item, state in (self.db.node | self.db.term).items():
            if state == EntityState.ACTIVE:
                item.setSelected(True)

    def delete_items(self, items: list[QGraphicsItem] | set[QGraphicsItem]):
        """
        Removes the specified items from the canvas and updates the database accordingly.
        :param items: A list or set of QGraphicsItem objects to be removed.
        """
        # Create a batch action:
        batch = BatchActions([])

        for item in items:
            if isinstance(item, Node):
                batch.add_to_batch(RemoveNodeAction(self, item))

            if isinstance(item, StreamTerminal):
                batch.add_to_batch(RemoveStreamAction(self, item))

        # Execute batch operation:
        if batch.size:  self.manager.do(batch)

    def find_items(self):
        """
        Finds an item in the canvas by its name or identifier.
        """
        usr_input = Getter("Search Item",
                           "Enter the item's identifier:",
                           self.views()[0],
                           Qt.WindowType.Popup)
        usr_input.open()

        # Connect the finished signal to set the tab text:
        usr_input.finished.connect(
            lambda: self.highlight(usr_input.text())
            if usr_input.result() and usr_input.text() else None
        )

    def rearrange(self):
        """
        Rearranges the terminals.
        """
        for terminal, state in self.db.term.items():

            if (
                state == EntityState.ACTIVE and
                terminal.handle.connected and
                terminal.handle.conjugate
            ):
                # Get the conjugate handle:
                conjugate = terminal.handle.conjugate
                scenepos  = terminal.handle.scenePos()
                terminal.moveBy(0, conjugate.scenePos().y() - scenepos.y())

    @validator
    def highlight(self, identifier: str):
        """
        Searches for an item in the canvas by its identifier.
        :param identifier: The identifier of the item to search for.
        """
        # First, deselect all items:
        self.deselect()

        # Search for the item in the node database:
        for node, state in self.db.node.items():
            if (
                state == EntityState.ACTIVE and
                node.name == identifier
            ):
                node.setSelected(True)
                view = self.views()[0]
                view.centerOn(node.scenePos())
                return

        # Search for the item in the terminal database:
        for term, state in self.db.term.items():
            if (
                state == EntityState.ACTIVE and
                term.name == identifier
            ):
                term.setSelected(True)
                view = self.views()[0]
                view.centerOn(term.scenePos())
                return

        # If no item is found, print a message:
        print(f"No item found with identifier '{identifier}'.")

    def deselect(self):
        """
        Deselects all items in the canvas.
        :return:
        """
        for item in self.selectedItems():
            item.setSelected(False)

    def import_project(self, filename: str | None = None):
        """
        Imports a project from a file. This method is called when the user selects the "Import Schema" action from the
        context menu or presses the corresponding keyboard shortcut.
        """
        # If no filename is provided, prompt the user to select a file:
        if not filename:
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getOpenFileName(self.views()[0],
                                                      "Export Schema", "",
                                                      "JSON Files (*.json);;All Files (*)")

        # If the filename is empty, return:
        if not filename:
            logging.info("No file selected for import.")
            return

        # Import the schematic from the specified file:
        with open(filename) as file:
            json_code = file.read()

        JsonIO.decode(self, json_code)

        self.sig_canvas_changed.emit(CanvasState.UNSAVED)
        self.sig_loaded_project.emit(Path(filename).stem)

    def export_project(self, filename: str | None = None):
        """
        Exports the current project to a file. This method is called when the user selects the "Export Schema" action from
        the context menu or presses the corresponding keyboard shortcut.
        :param filename: The name of the file to export to (optional).
        """
        # If no filename is provided, prompt the user to select a file:
        if  not filename:
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(self.views()[0],
                                                      "Export Schema", "",
                                                      "JSON Files (*.json);;All Files (*)")

        # If the filename is empty, return:
        if not filename:
            logging.info("No file selected for export.")
            return

        # Export the schematic to the specified file:
        json_code = JsonIO.encode(self)
        with open(filename, "w+") as file:
            file.write(json_code)

        # Emit signal:
        self.sig_canvas_changed.emit(CanvasState.SAVED)

    @pyqtSlot(name='on_item_removed')
    def on_item_removed(self):
        """
        Event handler called when an item is removed from the canvas.
        """
        item = self.sender()
        if  isinstance(item, QGraphicsObject) and item.scene() == self:
            self.delete_items([item])

        # Notify the application that the canvas has changed:
        self.sig_canvas_changed.emit(CanvasState.UNSAVED)