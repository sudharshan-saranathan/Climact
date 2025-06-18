import logging
import weakref

import numpy as np
import qtawesome as qta

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QtMsgType
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QColor
from PyQt6.QtWidgets import QMenu, QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QInputDialog, QMessageBox

from custom.message import Message
from custom.entity import Entity, EntityClass, EntityState, EntityRole, Evolution
from tabs.schema.graph.node import Node
from tabs.schema.graph.handle import Handle
from util import validator

class Table(QTableWidget):
    """
    Table widget to display the schema graph's variables and parameters.
    """
    # Signals:
    sig_table_modified = pyqtSignal(Node, bool)

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):
        super().__init__(parent)
        super().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # References and temporary objects:
        self._node = None       # Node reference.
        self._emap = None       # Entity map, needed to push user-modifications to entity's data.
        self._hmap = dict()     # Handle reference, needed to push user-modifications to handle's data.
        self._pmap = dict()     # Params reference, needed to push user-modifications to param's  data.
        self._save = False

        # Set headers:
        self.verticalHeader().setFixedWidth(24)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setColumnCount(len(kwargs.get("headers")))
        self.setHorizontalHeaderLabels(kwargs.get("headers"))

        # Adjust column sizes:
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Install shortcuts:
        shortcut_add_row = QShortcut(QKeySequence("Shift+="), self, lambda: self.add_entity(EntityClass.PAR))
        # shortcut_commit  = QShortcut(QKeySequence("Ctrl+Return"), self, self.commit)

        # Connect table's signals:
        self.cellChanged.connect(self.on_table_edited)
        self.customContextMenuRequested.connect(lambda event: self._menu.exec(event.globalPos()))

        # Initialize menu:
        self._init_menu()

    # Initialize menu:
    def _init_menu(self):

        self._menu = QMenu()
        eraser = self._menu.addAction(qta.icon('mdi.eraser', color='red')  , "Erase" , self.erase)
        assign = self._menu.addAction(qta.icon('mdi.equal' , color='green'), "Assign", self.assign)

        assign.setIconVisibleInMenu(True)
        eraser .setIconVisibleInMenu(True)

    # Create row to display variable data:
    @validator
    def add_entity(self, eclass: EntityClass, entity: Entity | None = None):
        """
        Create a row in the table to display the variable's data.

        :param eclass: The class of the entity (variable or parameter).
        :param entity: The variable to display.
        """

        # Call super-class's method (see QTableWidget documentation) to insert a new row:
        super().insertRow(self.rowCount())
        row_id = self.rowCount() - 1

        # Fetch icon depending on the entity class:
        icon   = qta.icon("mdi.alpha", color='black') if eclass == EntityClass.PAR else qta.icon("mdi.variable", color='black')
        symbol = str()      if entity is None else entity.symbol
        label  = str()      if entity is None else entity.label
        units  = str()      if entity is None else entity.units
        info   = str()      if entity is None else entity.info
        strid  = "Default"  if entity is None else entity.strid
        model  = "Unknown"  if entity is None else entity.model

        # Create TableWidgetItem for the variable:
        row_items = list()
        row_items.append(item_0 := QTableWidgetItem(icon, symbol))  # Symbol
        row_items.append(item_1 := QTableWidgetItem(label))         # Label
        row_items.append(item_2 := QTableWidgetItem(info ))         # Info
        row_items.append(item_3 := QTableWidgetItem(units))         # Units
        row_items.append(item_4 := QTableWidgetItem(strid))         # Strid
        row_items.append(item_5 := QTableWidgetItem(strid))         # Strid

        # Customize cell-behavior:
        if  eclass == EntityClass.VAR:
            item_4.setFlags(item_4.flags() & ~Qt.ItemFlag.ItemIsEditable)       # Make strid non-editable
            item_0.setFlags(item_0.flags() & ~Qt.ItemFlag.ItemIsEditable)       # Make symbol non-editable
            item_0.setData(Qt.ItemDataRole.UserRole, entity)    # Set user-role for symbol

        # Center align all cells:
        for column in range(1, self.columnCount()):
            row_items[column].setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Install cells in the table:
        self.setItem(row_id, 0, item_0)
        self.setItem(row_id, 1, item_1)
        self.setItem(row_id, 2, item_2)
        self.setItem(row_id, 3, item_3)
        self.setItem(row_id, 4, item_4)
        self.setItem(row_id, 4, item_5)

        # Store in the hash-map:
        if  eclass == EntityClass.VAR:
            self._hmap[row_id] = entity

        elif eclass == EntityClass.PAR:
            self._save = True
            self.sig_table_modified.emit(self._node(), self._save)

    # Delete selected rows:
    def delete(self):
        """
        Delete all selected rows in the table.
        :return:
        """
        # Get all selected rows:
        rows = set([item.row() for item in self.selectedItems()])

        # Sort in reverse order for `removeRow()` to work correctly:
        for row in sorted(rows, reverse=True):

            is_selected = True
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item:
                    is_selected &= item.isSelected()

            # Remove the row if it is selected:
            if is_selected: self.removeRow(row)

        # Notify manager:
        self._save = True
        self.sig_table_modified.emit(self._node(), self._save)

    # Fetch and display _node-data:
    def fetch(self, node: Node):
        """
        Fetch the node's data and display it in the table.
        :param node:
        """
        # Remove all rows, reset temporary objects:
        self.reset()

        # Store weak-reference and block signals:
        self._node = weakref.ref(node)
        self.blockSignals(True)             # Block signal (self.cellChanged()) from triggering slots when fetching _node data

        # Abort if the _node is None:
        if  self._node() is None:
            return

        for entity, state in node[EntityClass.VAR].items():
            if state == EntityState.ACTIVE:
                self.add_entity(EntityClass.VAR, entity)

        # Display the _node's parameters:
        for parameter in node[EntityClass.PAR]:
            self.add_entity(EntityClass.PAR, parameter)

        # Unblock signals:
        self.blockSignals(False)
        self.update()

    # Clear the table's contents:
    def reset(self):
        """
        Reset the table's contents, clearing all rows and temporary objects.
        :return:
        """
        self._node    = None
        self._save = False

        self._hmap.clear()
        self.setRowCount(0)

    # Assign selected cells:
    @pyqtSlot(name="Table.assign")
    def assign(self):
        """
        Assign a value to each selected item in the table.
        :return:
        """
        # Get an input value:
        value, code = QInputDialog.getText(self, "Assign", "Enter a value:")
            
        # Abort if the user cancels the dialog:
        if not code: return

        # Abort if the entered value is not a string, float, or int:
        if not isinstance(value, str | float | int):
            _error = Message(QtMsgType.QtCriticalMsg,
                             "The entered value must be of type `str`, `float`, or `int`")
            _error.exec()
            return

        # Assign the value to each selected item:
        for item in self.selectedItems():
            if item: item.setText(str(value))

    # Erase selected cells:
    @pyqtSlot(name="+erase")
    def erase(self):
        """
        Erase the text in each selected item in the table.
        """

        # Get selected items:
        selected_items = self.selectedItems()

        # Erase each selected item:
        for item in selected_items:
            item.setText("")

    def commit(self):
        """
        Commit the changes made in the table to the node's variables and parameters.
        :return:
        """
        # Abort if no _node has been set:
        if self._node() is None: return

        # Clear the _node's parameters and equations:
        self._node()[EntityClass.PAR].clear()

        # Save defined parameters:
        for row in range(self.rowCount()):

            # Update the node's variable(s):
            if row in self._hmap.keys():

                variable = self._hmap[row]
                variable.symbol = self.text_at(row, 0)
                variable.info   = self.text_at(row, 1)
                variable.units  = self.text_at(row, 2)
                variable.strid  = self.text_at(row, 3)

                # Assign model:
                try: variable.model = Evolution(self.text_at(row, 8).upper())
                except (ValueError, TypeError) as exception:
                    logging.warning("Unrecognized evolution-model", exception)

                if  variable.connected and variable.conjugate:
                    variable.conjugate.import_data(variable, exclude='symbol')

            # Update the node's parameters:
            else:
                entity = Entity(
                    EntityClass.PAR,
                    self.text_at(row, 0),
                     self.text_at(row, 3),
                )

                entity.info  = self.text_at(row, 1)
                entity.units = self.text_at(row, 2)

                # Add parameter to dictionary:
                self._node()[EntityClass.PAR].append(entity)

        # Notify manager:
        self._save = False
        self.sig_table_modified.emit(self._node(), self._save)

    def text_at(self, row, column):
        """
        Fetch the text from a specific cell in the table.
        :param row:
        :param column:
        """
        item = self.item(row, column)
        return item.text() if item else ""

    def on_table_edited(self, row: int, column: int):
        """
        Event-handler for when a cell's data is changed.
        :param row:
        :param column:
        """
        self._save = True
        self.sig_table_modified.emit(self._node(), self._save)
