import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGridLayout, QGraphicsItem, QTextEdit

from custom import EntityClass
from custom.configure import EntityConfigure
from tabs.database.selector import Selector, Charts
from tabs.schema.canvas import Canvas
from tabs.database.eqnview import EqnView
from tabs.database.table import Table
from tabs.database.tree import Tree
from tabs.schema.graph.node import Node
from util import validator


class DataManager(QWidget):
    """
    DataManager class for managing database interactions and displaying data.
    """
    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget | None):
        super().__init__(parent)

        # Save canvas reference:
        self._canvas = canvas

        # Main-widgets:
        self._editor = QTextEdit(self)
        self._config = EntityConfigure(None, self)
        self._eqview = EqnView(self._canvas, self)
        self._trview = Tree(self._canvas, self)
        self._sheets = Table(self, headers=['Symbol', 'Label', 'Description', 'Units', 'Category', 'Evolution'])

        # Connect signals to slots:
        self._trview.sig_item_selected.connect(self.on_tree_item_selected)

        # Layout:
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Customize the equation-editor:
        self._eqview.setEnabled(False)

        self._layout.addWidget(self._trview, 0, 0, 2, 1)
        self._layout.addWidget(self._sheets, 0, 1, 1, 2)
        self._layout.addWidget(self._eqview, 1, 1)
        self._layout.addWidget(self._config, 1, 2, Qt.AlignmentFlag.AlignRight)
        self._layout.setRowStretch(0, 2)
        self._layout.setColumnStretch(1, 2)

        # Connect signals:
        self._sheets.sig_table_modified.connect(self._trview.show_modification_status)

    # Clear data:
    def clear(self):
        """
        Clear the data manager, resetting all views and spreadsheets.
        :return:
        """
        self._sheets.reset()
        self._eqview.clear()

    # Reload data:
    def reload(self, _canvas: Canvas):
        """
        Reload the data manager with a new canvas.
        :param _canvas:
        """

        if  not isinstance(_canvas, Canvas):
            raise ValueError("Expected argument of type `Canvas`")

        # Store canvas reference:
        self._canvas = _canvas

        # Reset spreadsheets and equation-viewer:
        self._sheets.reset()
        self._eqview.clear()

        # Reload tree:
        self._trview.reload(self._canvas)

    # Tree-item selected:
    @validator
    def on_tree_item_selected(self, nuid: str, huid: str):
        """
        Handle the selection of a tree item.
        :param nuid:
        :param huid:
        :return:
        """
        # Find the node by unique identifier (nuid):
        node = next((node for node in self._canvas.db.node.keys() if node.uid == nuid), None)
        print(f"Displaying data for node: {node.uid} ({node.name})")

        # Display data for _node:
        self._sheets.setRowCount(0)
        self._sheets.fetch(node)

        # Enable the equation-editor:
        self._eqview.setEnabled(True)
        self._eqview.node = node