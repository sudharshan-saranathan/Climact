import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGridLayout, QGraphicsItem, QTextEdit, QLabel, QFormLayout, QLineEdit

from custom import EntityClass, EntityState
from tabs.schema.canvas import Canvas
from tabs.database.eqnlist import EqnList
from tabs.database.table import Table
from tabs.database.tree import Tree
from tabs.schema.graph.node import Node

class DataManager(QWidget):
    """
    DataManager class for managing database interactions and displaying data.
    """
    # Initializer:
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)

        # Main-widgets:
        self._label = QLabel("Equations Editor (Right-click to add or remove equations)")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("QLabel {"
                                  "margin: 2px;"
                                  "padding: 4px;"
                                  "background: #efefef;"
                                  "border-radius: 4px;"
                                  "border: 1px solid black;"
                                  "}")

        self._editor = QTextEdit(self)
        self._eqlist = EqnList(self)
        self._trview = Tree(self)
        self._sheets = Table(self, headers=['Symbol', 'Label', 'Description', 'Units', 'Category', 'Initial', 'Final', 'Model'])

        # Connect signals to slots:
        self._trview.sig_node_selected.connect(self.on_node_selected)

        # Layout:
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Customize the equation-editor:
        self._eqlist.setEnabled(False)

        self._layout.addWidget(self._trview, 0, 0, 3, 1)
        self._layout.addWidget(self._sheets, 0, 1, 1, 2)
        self._layout.addWidget(self._label , 1, 1, 1, 2)
        self._layout.addWidget(self._eqlist, 2, 1)
        self._layout.setRowStretch(0, 4)

        # Connect signals:
        self._sheets.sig_table_modified.connect(self._trview.show_modification_status)

    # Clear data:
    def clear(self):
        """
        Clear the data manager, resetting all views and spreadsheets.
        :return:
        """
        self._sheets.reset()
        self._eqlist.clear()

    # Reload data:
    def reload(self, canvas: Canvas):
        """
        Reload the data manager with a new canvas.
        :param canvas:
        """

        # Store canvas:
        self.setProperty('canvas', canvas)

        # Reset spreadsheets and equation-viewer:
        self._sheets.reset()
        self._eqlist.clear()

        # Reload tree:
        self._trview.reload(canvas)

    # Tree-item selected:
    def on_node_selected(self, node: Node):
        """
        Handle the selection of a tree item.
        :param node:
        :return:
        """
        if  not (canvas := self.property('canvas')):
            return

        # Display data for node:
        self._sheets.setRowCount(0)
        self._sheets.fetch(node)

        # Enable the equation-editor:
        self._eqlist.setEnabled(True)
        self._eqlist.node = node