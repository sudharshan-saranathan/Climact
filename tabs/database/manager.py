import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QGridLayout, QGraphicsView, QTextEdit, QLabel, QFormLayout, QLineEdit

from custom import EntityClass, EntityState
from tabs.schema.canvas import Canvas
from tabs.database.eqnlist import EqnList
from tabs.database.table import Table
from tabs.database.tree import Tree, SearchBar
from tabs.schema.graph.node import Node
from tabs.schema.graph.terminal import StreamTerminal

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

        self._eqlist = EqnList(self)
        self._trview = Tree(self)
        self._sheets = Table(self, headers=['Symbol', 'Label', 'Description', 'Units', 'Category', 'Initial', 'Final', 'Model'])

        self._search = SearchBar(self)
        self._search.setMinimumWidth(450)

        self._viewer = QGraphicsView(self)
        self._viewer.setStyleSheet("QGraphicsView {border: 1px solid black;}")
        self._viewer.horizontalScrollBar().setVisible(False)
        self._viewer.verticalScrollBar().setVisible(False)
        self._viewer.setRenderHint(QPainter.Antialiasing)
        self._viewer.setEnabled(False)

        # Connect signals to slots:
        self._trview.sig_node_selected.connect(self.on_node_selected)
        self._trview.sig_term_selected.connect(self.on_term_selected)
        self._search.editor.returnPressed.connect(lambda: self._trview.filter(self._search.editor.text()))

        # Layout:
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)

        # Customize the equation-editor:
        self._eqlist.setEnabled(False)

        self._layout.addWidget(self._trview, 0, 0, 1, 1)
        self._layout.addWidget(self._viewer, 1, 0, 1, 1)
        self._layout.addWidget(self._search, 2, 0, 1, 1, Qt.AlignmentFlag.AlignBottom)
        self._layout.addWidget(self._sheets, 0, 1)
        self._layout.addWidget(self._eqlist, 1, 1)
        self._layout.setRowStretch(0, 4)
        self._layout.setColumnStretch(1, 5)

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
        self._viewer.setScene(canvas)
        self._sheets.reset()
        self._eqlist.clear()

        # Reload tree:
        self._trview.reload(canvas)

    # Tree-item selected:
    def on_node_selected(self, node: Node):

        # Display data for node:
        node.setSelected(True)
        self._sheets.setRowCount(0)
        self._sheets.fetch(node)
        self._viewer.fitInView(node, Qt.AspectRatioMode.KeepAspectRatio)
        self._viewer.scale(0.6, 0.6)

        # Enable the equation-editor:
        self._eqlist.setEnabled(True)
        self._eqlist.node = node

    # Tree-item selected:
    def on_term_selected(self, term: StreamTerminal):

        # Display data for terminal:
        term.setSelected(True)
        self._eqlist.clear()
        self._sheets.setRowCount(0)
        self._viewer.fitInView(term, Qt.AspectRatioMode.KeepAspectRatio)
        self._viewer.scale(0.6, 0.6)
