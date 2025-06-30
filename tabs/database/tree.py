"""
tree.py
"""
import logging

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QBrush
from PyQt6.QtWidgets import QToolButton, QLineEdit, QTreeWidget, QHBoxLayout, QGridLayout, QWidget, QHeaderView, QTreeWidgetItem, QFrame

from custom import EntityClass, EntityState

from tabs.schema.canvas import Canvas
from tabs.schema.graph.node import Node
import qtawesome as qta

from tabs.schema.graph.terminal import StreamTerminal

class SearchBar(QFrame):
    """
    Search bar for the tree widget.
    """
    # Signals:
    sig_search = pyqtSignal(str)

    # Constructor:
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)

        # Style:
        self.setObjectName("NodeSearchBar")
        self.setStyleSheet(
            "#NodeSearchBar {"
            "background: transparent;"
            "}"
            "QLineEdit {"
            "border: 1px solid #ccc;"
            "}"
            "QToolButton:hover {"
            "background: #ffb947"
            "}"
        )

        # Create a frame for the search bar:
        self.editor = QLineEdit(self)
        self.button = QToolButton(self)
        self.shrink = QToolButton(self)
        self.expand = QToolButton(self)

        self.button.setEnabled(True)
        self.button.setIcon(qta.icon('mdi.magnify', color='black'))
        self.shrink.setIcon(qta.icon('mdi.chevron-up', color='black'))
        self.expand.setIcon(qta.icon('mdi.chevron-down', color='black'))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.button)
        layout.addWidget(self.editor)
        layout.addWidget(self.shrink)
        layout.addWidget(self.expand)

class Tree(QTreeWidget):
    """
    Tree widget to display the schema graph's nodes and their variables/parameters.
    """
    # Signals:
    sig_node_selected = pyqtSignal(Node)

    # Class constructor:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)
        super().setColumnCount(5)

        # Save canvas reference:
        self._canvas = None

        # Customize column-header and column-widths:
        self.setHeaderLabels(["Symbol", "Label", "Class", "Stream", "X_ID"])
        for column in range(2, self.columnCount()):
            self.header().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.header().resizeSection(column, 60)

        self.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header().setStretchLastSection(False)

        # Connect signals to slots:
        self.itemSelectionChanged.connect(self.on_item_selected)

    # Add the canvas's nodes as top-level items in the tree:
    def add_node_item(self, node: Node):
        """
        Add a top-level item for the given node.
        :param node:
        """
        # Create a top-level item:
        item = QTreeWidgetItem(self, [node.uid, node.title])
        item.setData(0, Qt.ItemDataRole.UserRole, node)             # Store reference

        item.setIcon(0, QIcon("rss/icons/checked.png"))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        # Fetch the _node's variable(s) and parameter(s):
        for entity, state in node[EntityClass.VAR].items():
            if  state == EntityState.ACTIVE:
                var_item = QTreeWidgetItem(item, [entity.symbol, entity.label, entity.eclass.name, entity.strid, entity.connector().symbol if entity.connected else str()])

                var_item.setData(0, Qt.ItemDataRole.UserRole, entity)
                var_item.setIcon(0, qta.icon('mdi.variable', color='darkgray'))
                var_item.setForeground(4, QBrush(entity.color))
                for column in range(1, 7):
                    var_item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

        for entity in node[EntityClass.PAR]:
            par_item = QTreeWidgetItem(item, [entity.symbol, entity.label, "-", entity.eclass.name])
            par_item.setData(0, Qt.ItemDataRole.UserRole, entity)
            par_item.setIcon(0, qta.icon('mdi.alpha', color='darkgray'))
            par_item.setForeground(4, QBrush(entity.color))
            for column in range(1, 7):
                par_item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

        # If the node was double-clicked, show its contents:
        if  node.double_clicked:
            item.setSelected(True)
            node.double_clicked = False  # Reset the double-clicked flag

    # Add the canvas's terminals as top-level items in the tree:
    def add_term_item(self, term: StreamTerminal):
        """
        Add the given terminal as a top-level item in the tree.
        :param term:
        """
        # Create a top-level item:
        item = QTreeWidgetItem(self, [term.handle.symbol,
                                      term.handle.label,
                                      term.handle.eclass.name,
                                      term.handle.strid,
                                      term.handle.connector().symbol if term.handle.connected else str()]
                               )

        item.setData(0, Qt.ItemDataRole.UserRole, term)  # Store the terminal in the item
        item.setIcon(0, qta.icon('mdi.power-plug', color='darkred'))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)
        for column in range(1, 6):
            item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

    # Reload
    def reload(self, canvas: Canvas):
        """
        Reload the tree with the current canvas data.
        :param canvas:
        """

        # Clear tree and dictionary:
        self._canvas = canvas
        self.clear()

        # Add top-level root:
        for node, state in self._canvas.node_db.items():
            if  state == EntityState.ACTIVE:
                self.add_node_item(node)
                node.double_clicked = False

        for term, state in self._canvas.term_db.items():
            if  state == EntityState.ACTIVE:
                self.add_term_item(term)

    def filter(self, node: str):
        """
        Filter the tree items based on the search term.
        :param node: Search term to filter nodes.
        """

        self.collapseAll()
        self.clearSelection()

        items = self.findItems(node, Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive, 0)
        if  not len(items):
            return

        self.expand(self.indexFromItem(items[0]))
        items[0].setSelected(True)

    # Handle item selection:
    def on_item_selected(self):
        """
        Event-handler for when a node in the tree is selected.
        """
        items = self.selectedItems()
        if  not len(items):
            return

        item = items[0].data(0, Qt.ItemDataRole.UserRole)
        if  isinstance(item, Node):
            self.sig_node_selected.emit(item)

    # Toggle modification status:
    def show_modification_status(self, node: Node, unsaved: bool):
        """
        Update the node's modification status icon in the tree.
        :param node:
        :param unsaved:
        """
        items = self.findItems(node.uid, Qt.MatchFlag.MatchExactly, 0)
        if  len(items) != 1:
            return

        if unsaved:   items[0].setIcon(0, QIcon("rss/icons/exclamation.png"))
        else:
            items[0].setIcon(0, QIcon("rss/icons/checked.png"))
            self.reload(self._canvas)