"""
tree.py
"""
import logging

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QBrush
from PyQt6.QtWidgets import QTreeWidget, QWidget, QHeaderView, QTreeWidgetItem, QFrame

from custom import EntityClass, EntityState, EntityRole

from tabs.schema.canvas import Canvas
from tabs.schema.graph.node import Node
import qtawesome as qta

from tabs.schema.graph.terminal import StreamTerminal
from util import validator


class Tree(QTreeWidget):
    """
    Tree widget to display the schema graph's nodes and their variables/parameters.
    """
    # Signals:
    sig_item_selected = pyqtSignal(str, str)

    # Class constructor:
    def __init__(self, canvas: Canvas, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)
        super().setColumnCount(6)
        super().setFixedWidth(450)

        # Save canvas reference:
        self._canvas = canvas

        # Customize column-header and column-widths:
        self.setHeaderLabels(["Symbol", "Label", "Role", "Class", "Stream", "X_ID"])
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
        item = QTreeWidgetItem(self, [node.uid, node.name])
        item.setData(0, Qt.ItemDataRole.UserRole, node)  # Store the node in the item

        item.setIcon(0, QIcon("rss/icons/checked.png"))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        # Fetch the _node's variable(s) and parameter(s):
        for entity, state in node[EntityClass.VAR].items():
            if  state == EntityState.ACTIVE:
                var_item = QTreeWidgetItem(item, [entity.symbol,
                                                  entity.label,
                                                  entity.role.name,
                                                  entity.eclass.name,
                                                  entity.strid,
                                                  entity.connector.symbol if entity.connected else str()]
                                           )
                var_item.setIcon(0, qta.icon('mdi.variable', color='darkgray'))
                var_item.setForeground(4, QBrush(entity.color))
                for column in range(1, 7):
                    var_item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

        for entity in node[EntityClass.PAR]:
            par_item = QTreeWidgetItem(item, [entity.symbol,
                                              entity.label,
                                              "",
                                              entity.eclass.name,
                                              str(),
                                              str(),
                                              str()]
                                       )
            par_item.setIcon(0, qta.icon('mdi.alpha', color='darkgray'))
            par_item.setForeground(4, QBrush(entity.color))
            for column in range(1, 7):
                par_item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

        # If the node was double-clicked, show its contents:
        if  node.open:
            item.setSelected(True)

    # Add the canvas's terminals as top-level items in the tree:
    def add_term_item(self, term: StreamTerminal):
        """
        Add the given terminal as a top-level item in the tree.
        :param term:
        """
        # Create a top-level item:
        item = QTreeWidgetItem(self, [term.handle.symbol,
                                      term.handle.label,
                                      term.handle.role.name,
                                      term.handle.eclass.name,
                                      term.handle.strid,
                                      term.handle.connector.symbol if term.handle.connected else str()]
                               )
        item.setIcon(0, qta.icon('mdi.power-plug', color='darkred'))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)
        for column in range(1, 6):
            item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)

    # Reload
    @validator
    def reload(self, canvas: Canvas):
        """
        Reload the tree with the current canvas data.
        :param canvas:
        """
        # Debugging:
        logging.info("Reloading graph-data")

        # Clear tree and dictionary:
        self.clear()

        # Add top-level root:
        for node, state in self._canvas.db.node.items():
            if  state == EntityState.ACTIVE:
                self.add_node_item(node)
                node.open = False

        for term, state in self._canvas.db.term.items():
            if  state == EntityState.ACTIVE:
                self.add_term_item(term)

    # Handle item selection:
    def on_item_selected(self):
        """
        Event-handler for when a node in the tree is selected.
        """
        items = self.selectedItems()
        if  not len(items):
            return

        top_level_item = items[0]
        if  top_level_item.parent() is None:  # Item is a top-level item:
            self.sig_item_selected.emit(top_level_item.text(0), None)

        else:
            self.sig_item_selected.emit(top_level_item.parent().text(0), top_level_item.text(0))

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





