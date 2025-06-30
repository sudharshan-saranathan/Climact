import logging
import weakref

import numpy as np
import qtawesome as qta

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QtMsgType
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon, QColor, QBrush
from PyQt6.QtWidgets import QMenu, QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QInputDialog, QMessageBox, \
    QLabel, QLineEdit, QComboBox

from custom.dialog import Dialog
from custom.entity import Entity, EntityClass, EntityState
from tabs.schema.graph.node import Node
from tabs.schema.graph.handle import Handle

class Table(QTableWidget):
    """
    Table widget to display the schema graph's variables and parameters.
    """
    # Signals:
    sig_table_modified = pyqtSignal(Node, bool)

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):
        super().__init__(parent)

        # References and temporary objects:
        self.setProperty('node', None)      # Node reference.
        self.setProperty('save', False)     # Flag to indicate if the table has been modified.

        # Set headers:
        self.verticalHeader().setVisible(False)
        self.setColumnCount(len(kwargs.get("headers")))
        self.setHorizontalHeaderLabels(kwargs.get("headers"))

        # Adjust column sizes:
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Install shortcuts:
        shortcut_add_row = QShortcut(QKeySequence("Shift+="), self, self.add_entity)
        shortcut_commit  = QShortcut(QKeySequence("Ctrl+Return"), self, self.commit)

        # Connect table's signals:
        self.cellChanged.connect(self.on_table_edited)
        self.cellClicked.connect(lambda row, column: print(f"Cell clicked at row {row}, column {column}"))

        # Initialize menu:
        self._init_menu()

    # Initialize menu:
    def _init_menu(self):

        self._menu = QMenu()
        assign = self._menu.addAction(qta.icon('mdi.equal' , color='darkgray'), "Assign", self.assign)
        eraser = self._menu.addAction(qta.icon('mdi.eraser', color='darkred'), "Erase" , self.erase)
        self._menu.addSeparator()

        delete = self._menu.addAction(qta.icon('mdi.delete', color='black'), "Delete Row", self.delete)
        assign.setIconVisibleInMenu(True)
        eraser.setIconVisibleInMenu(True)
        delete.setIconVisibleInMenu(True)

    def contextMenuEvent(self, event):
        self._menu.exec(event.globalPos())

    # Create row to display variable data:
    def add_entity(self, eclass: EntityClass = EntityClass.PAR, entity: Entity | None = None):
        """
        Create a row in the table to display the variable's data.

        :param eclass: The class of the entity (variable or parameter).
        :param entity: The variable to display.
        """

        # Call super-class's method (see QTableWidget documentation) to insert a new row:
        row_id = self.rowCount()
        self.insertRow(self.rowCount())
        self.insertRow(self.rowCount())
        self.insertRow(self.rowCount())

        # Fetch icon depending on the entity class:
        icon    = qta.icon("mdi.alpha", color='black') if eclass == EntityClass.PAR else qta.icon("mdi.variable", color='black')
        symbol  = str()      if entity is None else entity.symbol
        label   = str()      if entity is None else entity.label
        units   = str()      if entity is None else entity.units
        info    = str()      if entity is None else entity.info
        strid   = "Default"  if entity is None else entity.strid
        value   = str()      if entity is None else entity.value
        minimum = str()      if entity is None else entity.minimum
        maximum = str()      if entity is None else entity.maximum

        for row in range(3):
            model = QComboBox(self)
            model.addItems(["Constant", "Linear", "Power", "Sigmoid"])
            self.setCellWidget(row_id + row, self.columnCount() - 1, model)  # Set the combo-box in the last column

        # Create TableWidgetItem for the variable:
        row_items = list()
        row_items.append(item_0 := QTableWidgetItem(icon, symbol))  # Symbol
        row_items.append(item_1 := QTableWidgetItem(label))         # Label
        row_items.append(item_2 := QTableWidgetItem(info ))         # Info
        row_items.append(item_3 := QTableWidgetItem(units))         # Units
        row_items.append(item_4 := QTableWidgetItem(strid))         # Strid
        row_items.append(item_vi := QTableWidgetItem(value))        # Value (Initial)
        row_items.append(item_ni := QTableWidgetItem(minimum))      # Minimum (Initial)
        row_items.append(item_mi := QTableWidgetItem(maximum))      # Maximum (Initial)
        row_items.append(item_vf := QTableWidgetItem())             # Value (Final)
        row_items.append(item_nf := QTableWidgetItem())             # Minimum (Final)
        row_items.append(item_mf := QTableWidgetItem())             # Maximum (Final)

        item_vi.setIcon(qta.icon("mdi.equal", color='black'))
        item_vf.setIcon(qta.icon("mdi.equal", color='black'))
        item_ni.setIcon(qta.icon("mdi.greater-than", color='#8AA1B1'))
        item_nf.setIcon(qta.icon("mdi.greater-than", color='#8AA1B1'))
        item_mi.setIcon(qta.icon("mdi.less-than", color='#8AA1B1'))
        item_mf.setIcon(qta.icon("mdi.less-than", color='#8AA1B1'))

        # Customize behavior for variables:
        if  eclass == EntityClass.VAR:
            item_4.setFlags(item_4.flags() & ~Qt.ItemFlag.ItemIsEditable)       # Make strid non-editable
            item_1.setFlags(item_1.flags() & ~Qt.ItemFlag.ItemIsEditable)       # Make label non-editable
            item_0.setFlags(item_0.flags() & ~Qt.ItemFlag.ItemIsEditable)       # Make symbol non-editable
            item_0.setData(Qt.ItemDataRole.UserRole, entity)      # Store variable reference

        # Customize behavior for parameters:
        if  eclass == EntityClass.PAR:
            item_0.setFlags(item_0.flags() | Qt.ItemFlag.ItemIsEditable)                # Make parameter-symbols editable
            item_0.setData(Qt.ItemDataRole.UserRole, entity or Entity())    # Store parameter reference

        # Center align all cells:
        for column in range(0, 5):
            row_items[column].setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Install cells in the table:
        self.setItem(row_id, 0, item_0)
        self.setItem(row_id, 1, item_1)
        self.setItem(row_id, 2, item_2)
        self.setItem(row_id, 3, item_3)
        self.setItem(row_id, 4, item_4)
        self.setItem(row_id, 5, item_vi)
        self.setItem(row_id + 1, 5, item_ni)
        self.setItem(row_id + 2, 5, item_mi)
        self.setItem(row_id, 6, item_vf)
        self.setItem(row_id + 1, 6, item_nf)
        self.setItem(row_id + 2, 6, item_mf)

        # Span the first five columns across the rows:
        for column in range(5):
            self.setSpan(row_id, column, 3, 1)  # Span each cell in the first five columns across the row

    # Delete selected rows:
    def delete(self):
        """
        Delete all selected rows in the table.
        :return:
        """

        # Get all selected rows:
        modified = False
        selected = {item.row() for item in self.selectedItems()}
        grouped  = set()

        # Group rows by their base row (every three rows correspond to a variable or parameter):
        for row in selected:
            base = row - (row % 3)                      # Calculate the base row
            grouped.update([base, base + 1, base + 2])  # Add the base row and the next two rows

        # Sort in reverse order for `removeRow()` to work correctly:
        for row in sorted(grouped, reverse=True):
            self.removeRow(row + 2)         # Remove row from the table
            self.removeRow(row + 1)         # Remove the next row (minimum)
            self.removeRow(row)             # Remove the next row (maximum)
            modified |= True

        # Notify manager:
        if  modified:
            self.setProperty('save', modified)
            self.sig_table_modified.emit(self.property('node'), modified)

    # Fetch and display _node-data:
    def fetch(self, node: Node):
        """
        Fetch the node's data and display it in the table.
        :param node:
        """

        self.reset()
        self.blockSignals(True)
        self.setProperty('node', node)

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
        self.setProperty('node', None)
        self.setProperty('save', False)
        self.setRowCount(0)

    # Assign selected cells:
    @pyqtSlot(name="assign")
    def assign(self):
        """
        Assign a value to each selected item in the table.
        :return:
        """
        # Get an input value:
        value, code = QInputDialog.getText(self, "Assign", "Enter a value:")

        # Abort if the user cancels the dialog:
        if not code: return

        # Assign the value to each selected item:
        [item.setText(str(value)) for item in self.selectedItems()]

    # Erase selected cells:
    @pyqtSlot(name="erase")
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

        parameters = list()

        # Read tabular data and update the node's variables and parameters:
        for row in range(0, self.rowCount(), 3):
            entity = self.item(row, 0).data(Qt.ItemDataRole.UserRole)
            eclass = entity.eclass

            if  eclass == EntityClass.PAR:
                entity.symbol  = self.text_at(row, 0)
                entity.label   = self.text_at(row, 1)
                entity.info    = self.text_at(row, 2)
                entity.units   = self.text_at(row, 3)
                entity.strid   = self.text_at(row, 4)
                entity.value   = self.text_at(row, 5)
                entity.minimum = self.text_at(row + 1, 5)
                entity.maximum = self.text_at(row + 2, 5)

            else:
                entity.info = self.text_at(row, 2)
                entity.units = self.text_at(row, 3)
                entity.value = self.text_at(row, 5)
                entity.minimum = self.text_at(row + 1, 5)
                entity.maximum = self.text_at(row + 2, 5)

                if  entity.connected:
                    entity.clone_into(entity.conjugate())

            self.property('node')[eclass][entity] = EntityState.ACTIVE

        # Notify manager:
        self.setProperty('save', False)
        self.sig_table_modified.emit(self.property('node'), False)

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
        self.setProperty('save', True)
        self.sig_table_modified.emit(self.property('node'), True)