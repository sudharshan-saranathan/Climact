import weakref

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon
from PyQt6.QtWidgets import QTableWidget, QWidget, QHeaderView, QTableWidgetItem

from custom.dialog import Dialog
from custom.entity import Entity, EntityClass, EntityState
from tabs.schema.graph import Node, Handle

class Table(QTableWidget):

    # Signals:
    sig_table_modified = pyqtSignal(Node, bool)

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # References and temporary objects:
        self._node = None
        self._hmap = dict()     # Handle reference, needed to push user-modifications to handle's data
        self._pmap = dict()     # Params reference, needed to push user-modifications to params'  data
        self._cmap = dict()     # Row reference, needed during copy-paste operations
        self._unsaved = False

        # Set headers:
        self.setCornerButtonEnabled(False)
        self.verticalHeader().setFixedWidth(24)
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setColumnCount(len(kwargs.get("headers")))
        self.setHorizontalHeaderLabels(kwargs.get("headers"))

        # Adjust column sizes:
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        # Install shortcuts:
        shortcut_add_row = QShortcut(QKeySequence("Shift+="), self)
        shortcut_del_row = QShortcut(QKeySequence("Delete" ), self)
        shortcut_commit  = QShortcut(QKeySequence("Ctrl+Return"), self)

        # Connect shortcuts:
        shortcut_add_row.activated.connect(self.add_params)
        shortcut_commit.activated .connect(self.commit)

        # Connect table's signals:
        self.cellChanged.connect(self.on_data_changed)

    # Create row to display variable data:
    def add_stream(self, handle: Handle):

        # Call the base-class implementation first:
        row = self.rowCount()
        super().insertRow(row)

        # Create QTableWidgetItems:
        symb_item = QTableWidgetItem(QIcon("rss/icons/variable.png"), handle.symbol)
        symb_item.setFlags(symb_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        symb_item.setData(Qt.ItemDataRole.UserRole, "Variable")

        name_item = QTableWidgetItem(handle.info)
        unit_item = QTableWidgetItem(handle.units)
        unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        type_item = QTableWidgetItem(handle.strid)
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        value_item = QTableWidgetItem(str(handle.value))
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        sigma_item = QTableWidgetItem(str(handle.sigma))
        sigma_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        lower_item = QTableWidgetItem(str(handle.minimum))
        lower_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        upper_item = QTableWidgetItem(str(handle.maximum))
        upper_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Install cells:
        self.setItem(row, 0, symb_item)
        self.setItem(row, 1, name_item)
        self.setItem(row, 2, unit_item)
        self.setItem(row, 3, type_item)
        self.setItem(row, 4, value_item)
        self.setItem(row, 7, sigma_item)
        self.setItem(row, 5, lower_item)
        self.setItem(row, 6, upper_item)

        # Store in hash-map:
        self._hmap[row] = handle

    # Create row for new parameter:
    def add_params(self, entity: Entity = Entity()):

        # Create parameter
        row = self.rowCount()
        super().insertRow(row)

        # Create QTableWidgetItems:
        symb_item = QTableWidgetItem(QIcon("rss/icons/parameter.png"), entity.symbol)
        symb_item.setData(Qt.ItemDataRole.UserRole, "Parameter")

        name_item = QTableWidgetItem(entity.info)
        unit_item = QTableWidgetItem(entity.units)
        unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        type_item = QTableWidgetItem(entity.strid)
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        value_item = QTableWidgetItem(str(entity.value))
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        sigma_item = QTableWidgetItem(str(entity.sigma))
        sigma_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        lower_item = QTableWidgetItem(str(entity.minimum))
        lower_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        upper_item = QTableWidgetItem(str(entity.maximum))
        upper_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setItem(row, 0, symb_item)
        self.setItem(row, 1, name_item)
        self.setItem(row, 2, unit_item)
        self.setItem(row, 3, type_item)
        self.setItem(row, 4, value_item)
        self.setItem(row, 7, sigma_item)
        self.setItem(row, 5, lower_item)
        self.setItem(row, 6, upper_item)

        # Notify manager:
        self._unsaved = True
        self.sig_table_modified.emit(self._node(), self._unsaved)

    # Fetch and display node-data:
    def fetch(self, node: Node):

        # Remove all rows, reset temporary objects:
        self.reset()

        # Store weak-reference and block signals:
        self._node = weakref.ref(node)
        self.blockSignals(True)             # Block signal (self.cellChanged()) from triggering slots when fetching node data

        # Abort if the node is None:
        if self._node() is None:
            return

        # Display the node's variables:
        for variable, state in node[EntityClass.VAR].items():
            if state == EntityState.ACTIVE:
                self.add_stream(variable)

        # Display the node's parameters:
        for parameter, state in node[EntityClass.PAR].items():
            if state == EntityState.ACTIVE:
                self.add_params(parameter)

        # Unblock signals:
        self.blockSignals(False)

    # Clear the table's contents:
    def reset(self):
        self._node    = None
        self._unsaved = False

        self._hmap.clear()
        self.setRowCount(0)

    # Method to return unique column-values:
    def unique(self, column: int):

        if column >= self.columnCount():
            return None

        fields = set()
        for row in range(self.rowCount()):
            if self.item(row, column):
                fields.add(self.item(row, column).text())

        return fields

    def commit(self):

        # Abort if no node has been set:
        if self._node() is None: return

        # Clear the node's parameters and equations:
        self._node()[EntityClass.PAR].clear()

        # Save defined parameters:
        for row in range(self.rowCount()):

            # Update the node's variable(s):
            if row in self._hmap.keys():

                variable = self._hmap[row]
                variable.symbol  = self.cell_data(row, 0)
                variable.info    = self.cell_data(row, 1)
                variable.units   = self.cell_data(row, 2)
                variable.strid   = self.cell_data(row, 3)
                variable.value   = self.cell_data(row, 4)
                variable.sigma   = self.cell_data(row, 7)
                variable.minimum = self.cell_data(row, 5)
                variable.maximum = self.cell_data(row, 6)

                if variable.connected and variable.conjugate:

                    conjugate = variable.conjugate()
                    conjugate.symbol  = self.cell_data(row, 0)
                    conjugate.info    = self.cell_data(row, 1)
                    conjugate.units   = self.cell_data(row, 2)
                    conjugate.strid   = self.cell_data(row, 3)
                    conjugate.value   = self.cell_data(row, 4)
                    conjugate.sigma   = self.cell_data(row, 7)
                    conjugate.minimum = self.cell_data(row, 5)
                    conjugate.maximum = self.cell_data(row, 6)

            # Update the node's parameters:
            else:
                entity = Entity()
                entity.eclass  = EntityClass.PAR
                entity.symbol  = self.cell_data(row, 0)
                entity.info    = self.cell_data(row, 1)
                entity.units   = self.cell_data(row, 2)
                entity.strid   = self.cell_data(row, 3)
                entity.value   = self.cell_data(row, 4)
                entity.minimum = self.cell_data(row, 5)
                entity.maximum = self.cell_data(row, 6)
                entity.sigma   = self.cell_data(row, 7)

                # Add parameter to dictionary:
                self._node()[EntityClass.PAR, entity] = EntityState.ACTIVE

        # Notify manager:
        self._unsaved = False
        self.sig_table_modified.emit(self._node(), self._unsaved)

    def cell_data(self, row, column):
        item = self.item(row, column)
        return item.text() if item else ""

    def on_data_changed(self, row: int, column: int):
        self._unsaved = True
        self.sig_table_modified.emit(self._node(), self._unsaved)
