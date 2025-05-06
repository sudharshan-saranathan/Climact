import logging

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QTreeWidget, QWidget, QHeaderView, QTreeWidgetItem

from tabs.schema.canvas import Canvas
from tabs.schema.graph import Node, StreamType

class Tree(QTreeWidget):

    # Signals:
    sig_item_selected = pyqtSignal(str, str)

    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Save canvas reference:
        self._canvas = canvas

        # Customize column-header:
        self.setHeaderLabels(["ID", "NAME", "ATTR"])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Customize attribute(s):
        self.setFixedWidth(480)
        self.setColumnCount(3)

        # Connect to slot:
        self.itemSelectionChanged.connect(self.on_item_selected)

    # Reload
    def reload(self):

        # Clear tree and dictionary:
        self.clear()

        # Top-level items:
        logging.info("Reloading graph-data")
        for node in self._canvas.node_items:
            if  self._canvas.node_items[node]:
                self.add_root_item(node)

    # Add top-level root:
    def add_root_item(self, node: Node):

        # Create a top-level item:
        item = QTreeWidgetItem(self, [node.uid, node.name, "None"])
        item.setIcon(0, QIcon("rss/icons/checked.png"))
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        # Fetch the node's variable(s) and parameter(s):
        for variable in node.variables:

            stream = "Input" if variable.stream == StreamType.INP else "Output"
            var_item = QTreeWidgetItem(item, [variable.symbol, variable.label, stream])
            var_item.setIcon(0, QIcon("rss/icons/variable.png"))
            var_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            var_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        for parameter in node[StreamType.PAR]:

            par_item = QTreeWidgetItem(item, [parameter.symbol, "StreamType.PAR"])
            par_item.setIcon(0, QIcon("rss/icons/parameter.png"))
            par_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            par_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

    # Handle item selection:
    def on_item_selected(self):

        items = self.selectedItems()
        if not len(items):
            return

        top_level_item = items[0]
        if top_level_item.parent() is None:  # Item is a top-level item:
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





