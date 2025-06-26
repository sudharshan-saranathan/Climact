import logging

from PyQt6.QtWidgets import QWidget, QGridLayout

from tabs.schema.canvas import Canvas
from tabs.database.eqnlist import EqnList
from tabs.database.table import Table
from tabs.database.tree import Tree
from custom.entity import EntityState

class DataManager(QWidget):

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Set properties:
        self.setProperty("canvas", None)
        self.setProperty("title" , "Node-data Manager")

        # Main-widgets:
        self._eqns = EqnList(self)
        self._tree = Tree(self)
        self._data = Table(self, headers=['Symbol', 'Description', 'Units', 'Category', 'Value', 'Lower', 'Upper', 'Sigma', 'Interpolation', 'Auto'])

        # Connect signals to slots:
        self._tree.sig_item_selected.connect(self.on_tree_item_selected)

        # Layout:
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Customize the equation-editor:
        self._eqns.setFixedHeight(240)
        self._eqns.setEnabled(False)

        self._layout.addWidget(self._tree, 0, 0, 3, 1)
        self._layout.addWidget(self._data, 0, 1, 2, 1)
        self._layout.addWidget(self._eqns, 2, 1)

        # Connect signals:
        self._data.sig_table_modified.connect(self._tree.show_modification_status)

    # Clear data:
    def clear(self):
        self._data.reset()
        self._eqns.clear()

    # Reload data:
    def reload(self, canvas: Canvas):

        # Store reference to the canvas:
        self.setProperty("canvas", canvas)

        # Reload tree:
        self._tree.reload(canvas)

        # Reset spreadsheets and equation-viewer:
        self._data.reset()
        self._eqns.clear()

    # Tree-item selected:
    def on_tree_item_selected(self, nuid: str, huid: str):

        # Find the node by unique identifier (nuid):
        for node, state in self.property("canvas").node_db.items():
            if state and node.uid == nuid:

                # Display data for _node:
                self._data.fetch(node)
                self._eqns.setEnabled(True)
                self._eqns.node = node