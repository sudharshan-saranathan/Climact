import logging

from PyQt6.QtWidgets import QWidget, QGridLayout

from tabs.schema.canvas import Canvas
from tabs.sheets.eqnview import EqnView
from tabs.sheets.table import Table
from tabs.sheets.tree import Tree

class DatabaseManager(QWidget):

    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Save canvas reference:
        self._canvas = canvas
        logging.info(f"Storing reference for Canvas {self._canvas.objectName()}")

        # Main-widgets:
        self._trview = Tree(self._canvas, self)
        self._eqview = EqnView(self)
        self._sheets = Table(self, headers=['Symbol', 'Description', 'Units', 'Category',
                                                    'Value', 'Lower', 'Upper' , 'Sigma',
                                                    'Interpolation', 'Auto'])

        # Connect signals to slots:
        self._trview.sig_item_selected.connect(self.on_tree_item_selected)
        self._canvas.sig_canvas_cleared.connect(self.clear)

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

    @property # Get active canvas:
    def canvas(self):   return self._canvas

    @canvas.setter # Set active canvas:
    def canvas(self, _canvas):
        if not isinstance(_canvas, Canvas):
            raise TypeError("Expected argument of type `Canvas`")

        # Store reference:
        self._canvas = _canvas

    # Clear data:
    def clear(self):
        self._sheets.reset()
        self._eqview.clear()

    # Reload data:
    def reload(self):
        self._trview.canvas = self._canvas
        self._trview.reload(self._canvas)
        self.clear()

    # Tree-item selected:
    def on_tree_item_selected(self, nuid: str,):

        # Find node using UID:
        node = self._canvas.find_node_by_uid(nuid)

        # Display data for node:
        self._sheets.setRowCount(0)
        self._sheets.fetch(node)

        # Enable the equation-editor:
        self._eqview.setEnabled(True)
        self._eqview.node = node