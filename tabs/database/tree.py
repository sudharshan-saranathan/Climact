import logging

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QTreeWidget, QWidget, QHeaderView, QTreeWidgetItem

from custom import EntityClass, EntityState

from tabs.schema.canvas import Canvas
from tabs.schema.graph import Node

class Tree(QTreeWidget):

    # Signals:
    sig_item_selected = pyqtSignal(str, str)

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Customize column-header:
        self.setHeaderLabels(["SYMBOL", "NAME", "ROLE/CLASS", "CONNECTOR"])
        self.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header().setStretchLastSection(False)

        # Customize attribute(s):
        self.setFixedWidth(480)
        self.setColumnCount(4)

        # Connect to slot:
        self.itemSelectionChanged.connect(self.on_item_selected)

    def reload(self, canvas: Canvas):

        # Clear tree and dictionary:
        self.clear()

        # Add top-level root:
        for node, state in canvas.node_db.items():
            if  state == EntityState.HIDDEN:
                continue

            if  node.double_clicked:
                item.setSelected(True)
                node.double_clicked = False  # Reset double-clicked state

    # Add top-level root:
    def add_node_item(self, node: Node):

        # Create a top-level item:
        item = QTreeWidgetItem(self, [node.uid, node.title, None, None])
        item.setIcon(0, QIcon("rss/icons/checked.png"))
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        # Fetch the _node's variable(s) and parameter(s):
        for variable, state in node[EntityClass.VAR].items():
            if state == EntityState.ACTIVE:
                var_item = QTreeWidgetItem(item, [variable.symbol, variable.label, variable.eclass.name, variable.connector().symbol if variable.connector else ""])
                var_item.setIcon(0, QIcon("rss/icons/variable.png"))
                var_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
                var_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
                var_item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)

        for parameter in node[EntityClass.PAR]:
            par_item = QTreeWidgetItem(item, [parameter.symbol, parameter.label, parameter.eclass.name, None])
            par_item.setIcon(0, QIcon("rss/icons/parameter.png"))
            par_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            par_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
            par_item.setTextAlignment(3, Qt.AlignmentFlag.AlignCenter)

        return item

    # Handle item selection:
    def on_item_selected(self):

        items = self.selectedItems()
        if  not len(items):
            return

        top_level_item = items[0]
        if  top_level_item.parent() is None:  # Item is a top-level item:
            self.sig_item_selected.emit(top_level_item.text(0), None)
            print(f"Tree.on_item_selected(): {top_level_item.text(0)} selected")

        else:
            self.sig_item_selected.emit(top_level_item.parent().text(0), top_level_item.text(0))
            print(f"Tree.on_item_selected(): {top_level_item.text(0)} selected")

    # Toggle modification status:
    def show_modification_status(self, node: Node, unsaved: bool):

        items = self.findItems(node.uid, Qt.MatchFlag.MatchExactly, 0)
        if len(items) != 1:
            return

        if unsaved  :   items[0].setIcon(0, QIcon("rss/icons/exclamation.png"))
        else        :   items[0].setIcon(0, QIcon("rss/icons/checked.png"))





