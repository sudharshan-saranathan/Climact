import logging

from PyQt6.QtWidgets import QWidget, QGridLayout

from tabs.schema.canvas import Canvas
from tabs.database.eqnview import EqnView
from tabs.database.table import Table
from tabs.database.tree import Tree

class DataManager(QWidget):

    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Save canvas reference:
        self._canvas = canvas

        # Main-widgets:
        self._eqview = EqnView(self._canvas, self)
        self._trview = Tree(self._canvas, self)
        self._sheets = Table(self, headers=['Symbol', 'Description', 'Units', 'Category',
                                                    'Value', 'Lower', 'Upper' , 'Sigma',
                                                    'Interpolation', 'Auto'])

        # Connect signals to slots:
        self._trview.sig_item_selected.connect(self.on_tree_item_selected)

        # Layout:
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Customize the equation-editor:
        self._eqview.setFixedHeight(250)
        self._eqview.setEnabled(False)

        self._layout.addWidget(self._trview, 0, 0, 3, 1)
        self._layout.addWidget(self._sheets, 0, 1, 2, 1)
        self._layout.addWidget(self._eqview, 2, 1)

        # Connect signals:
        self._sheets.sig_table_modified.connect(self._trview.show_modification_status)

    # Clear data:
    def clear(self):
        self._sheets.reset()
        self._eqview.clear()

    # Reload data:
    def reload(self, _canvas: Canvas):

        if not isinstance(_canvas, Canvas):
            raise ValueError("Expected argument of type `Canvas`")

        # Store canvas reference:
        self._canvas = _canvas

        # Reload tree:
        self._trview.reload(self._canvas)

        # Reset spreadsheets and equation-viewer:
        self._sheets.reset()
        self._eqview.clear()

    # Tree-item selected:
    def on_tree_item_selected(self, nuid: str, huid: str):

        # Find node using UID:
        node = self._canvas.find_node(nuid)

        # Display data for node:
        self._sheets.setRowCount(0)
        self._sheets.fetch(node)

        # Enable the equation-editor:
        self._eqview.setEnabled(True)
        self._eqview.node = node