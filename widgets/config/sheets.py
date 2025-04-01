from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem, QWidget, \
    QMenu

from core.core_qss import QSS
from widgets.schema.graph import Stream
from widgets.schema.graph.handle import Handle, Resource
from widgets.schema.graph.vertex import Node
from widgets.config.eqlist import Eqlist


def convert_to_float(arg: str):

    try:
        return float(arg)

    except ValueError:
        return None

class Header(QHeaderView):

    # Signals:
    sig_action_copy   = pyqtSignal(name="Copy")
    sig_action_paste  = pyqtSignal(name="Paste")
    sig_action_insert = pyqtSignal(name="Insert Row")
    sig_action_delete = pyqtSignal(name="Delete Row")

    # Constructor:
    def __init__(self, orientation: Qt.Orientation):

        # Initialize base-class:
        super().__init__(orientation)

        # Make sections clickable (to enable selections):
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Initialize menu:
        self.__menu__()

    def __menu__(self):

        self._menu = QMenu()
        self._menu.setTitle("Table Actions")

        if self.orientation() == Qt.Orientation.Horizontal:
            _set_value = self._menu.addAction("Set Value")
            _reset     = self._menu.addAction("Reset")

        else:
            _copy   = self._menu.addAction("Copy")
            _paste  = self._menu.addAction("Paste")

            self._menu.addSeparator()
            _insert = self._menu.addAction("Insert")
            _insert = self._menu.addAction("Delete")

            _copy  .triggered.connect(self.sig_action_copy.emit)
            _paste .triggered.connect(self.sig_action_paste.emit)
            _insert.triggered.connect(self.sig_action_insert.emit)

    def contextMenuEvent(self, event):

        actions  = self._menu.actions()
        parent   = self.parentWidget()
        position = self.mapToGlobal(event.pos())

        if not isinstance(parent, QTableWidget):
            return

        selected = bool(len(parent.selectedItems()))
        for action in actions:
            action.setEnabled(selected)

        # Display menu:
        self._menu.exec(position)

        # Call super-class implementation:
        super().contextMenuEvent(event)

class Sheets(QTableWidget):

    # Signals:
    sig_insert_equations = pyqtSignal(list, name="Signal emitted to insert equations")
    sig_notify_config    = pyqtSignal(str , name="Signal emitted to display a message")
    sig_data_modified    = pyqtSignal(Node, bool, name="Signal emitted when spreadsheet is modified")

    # Item map, and clipboard:
    __hmap = {}
    __cmap = {}
    __node = None
    __modified = False
    __autosave = True
    __eqwidget = None

    # Constructor:
    def __init__(self,
                 parent     : QWidget | None,
                 eqwidget   : Eqlist  | None,
                 **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # Setup keywords:
        cols = kwargs.get("columns")
        hdrs = kwargs.get("headers")

        # Save equations widget:
        self.__eqwidget = eqwidget
        self.__eqwidget.itemChanged.connect(lambda: self.sig_data_modified.emit(self.__node, True))

        # Set sorting enabled:
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setVisible(True)  # Ensure it's visible
        self.verticalHeader().setFixedWidth(24)

        if not cols:
            return

        # Customize horizontal header:
        self.setColumnCount(cols)
        self.setHorizontalHeaderLabels(hdrs)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalHeader().setSectionResizeMode(0 , QHeaderView.ResizeMode.Fixed)               # ID
        self.horizontalHeader().setSectionResizeMode(1 , QHeaderView.ResizeMode.Fixed)               # Symbol
        self.horizontalHeader().setSectionResizeMode(2 , QHeaderView.ResizeMode.Stretch)             # Description
        self.horizontalHeader().setSectionResizeMode(3 , QHeaderView.ResizeMode.Fixed)               # Units
        self.horizontalHeader().setSectionResizeMode(4 , QHeaderView.ResizeMode.Fixed)               # Category
        self.horizontalHeader().setSectionResizeMode(5 , QHeaderView.ResizeMode.Fixed)               # Lower limit
        self.horizontalHeader().setSectionResizeMode(6 , QHeaderView.ResizeMode.Fixed)               # Upper limit
        self.horizontalHeader().setSectionResizeMode(7 , QHeaderView.ResizeMode.Fixed)               # Delta
        self.horizontalHeader().setSectionResizeMode(8 , QHeaderView.ResizeMode.Fixed)               # Sigma
        self.horizontalHeader().setSectionResizeMode(9 , QHeaderView.ResizeMode.ResizeToContents)    # Interpolation
        self.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)    # Auto-balance

        # Customize column widths:
        self.setColumnWidth(0, 80)
        self.setColumnWidth(1, 65)
        self.setColumnWidth(3, 50)
        self.setColumnWidth(4, 80)
        self.setColumnWidth(5, 70)
        self.setColumnWidth(6, 70)
        self.setColumnWidth(7, 70)
        self.setColumnWidth(8, 70)
        self.setColumnWidth(9, 90)

        self.horizontalHeaderItem(10).setCheckState(Qt.CheckState.Checked)
        self.horizontalHeaderItem(10).setFlags(self.horizontalHeaderItem(9).flags() | Qt.ItemFlag.ItemIsUserCheckable)

        # Setup shortcuts:
        ctrl_c = QShortcut(QKeySequence("Ctrl+C"), self)
        ctrl_v = QShortcut(QKeySequence("Ctrl+V"), self)
        shift_add = QShortcut(QKeySequence(Qt.Key.Key_Plus), self)
        shift_del = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)

        # Connect shortcuts to slots:
        ctrl_c.activated.connect(self.on_copy )
        ctrl_v.activated.connect(self.on_paste)
        shift_add.activated.connect(self.on_insert_row)
        shift_del.activated.connect(self.on_delete_row)

        # Connect cellChanged() signal to slot:
        self.cellChanged.connect(self.on_data_changed)

    def __menu__(self):

        self._menu  = QMenu(self)
        _insert_row = self._menu.addAction("Insert Row")
        _delete_row = self._menu.addAction("Delete Row")

    @pyqtSlot(name="Sheets.commit")
    def commit(self):

        if self.__node is None or not len(self.__hmap):
            return

        par = list()
        for row in range(self.rowCount()):

            item   = self.item(row, 0)
            if item and item.text().startswith('H'):

                handle = self.__hmap[row]
                value = convert_to_float(self.item(row, 5).text())
                lower = convert_to_float(self.item(row, 6).text())
                upper = convert_to_float(self.item(row, 7).text())
                sigma = convert_to_float(self.item(row, 8).text())
                handle.info = self.item(row, 2).text()
                handle.unit = self.item(row, 3).text()

                print(f"Handle data: {value} {lower} {upper} {sigma}")
                handle.value = handle.value if value is None else value
                handle.lower = handle.lower if lower is None else lower
                handle.upper = handle.upper if upper is None else upper
                handle.sigma = handle.sigma if sigma is None else sigma

            elif item and item.text().startswith('L'):

                resource = Resource()
                resource.id       = self.item(row, 0).text()
                resource.symbol   = self.item(row, 1).text()
                resource.info     = self.item(row, 2).text()
                resource.unit     = self.item(row, 3).text()
                resource.category = self.item(row, 4).text()
                resource.value    = convert_to_float(self.item(row, 5).text())
                resource.lower    = convert_to_float(self.item(row, 6).text())
                resource.upper    = convert_to_float(self.item(row, 7).text())
                resource.sigma    = convert_to_float(self.item(row, 8).text())
                par.append(resource)

        self.__modified = True
        self.__node[Stream.PAR] = par.copy()
        self.__node.equations = self.__eqwidget.fetch_equations()

        nvar = len(self.__node[Stream.INP] + self.__node[Stream.OUT])
        npar = len(self.__node[Stream.PAR])
        neqn = len(self.__node.equations)

        self.__modified = False
        self.sig_notify_config.emit(f"Node {self.__node.nuid()} updated ({nvar} handles, {npar} parameters, {neqn} equations")
        self.sig_data_modified.emit(self.__node, self.__modified)

    @pyqtSlot(Node, name="Sheets.fetch")
    def fetch(self, node: Node):

        # If node isn't a valid Node, return:
        if not isinstance(node, Node):
            print(f"INFO: Invalid argument to Sheets.fetch(...)")
            return

        # Before fetching, block the widget's signals to ignore programmatic changes to cell data:
        # Do not remove this line:
        self.blockSignals(True)

        # Clear table and temporary objects:
        self.__hmap = {}
        self.setRowCount(0)

        # Store a reference to the node:
        self.__node = node

        # Fetch handle data:
        for handle in node[Stream.INP] + node[Stream.OUT]:
            self.insert_row()
            self.create_var(handle)

        # Fetch parameter data:
        for parameter in node[Stream.PAR]:
            self.insert_row()
            self.create_par(parameter)

        self.__eqwidget.clear()
        self.__eqwidget.insert_equations(self.__node.equations)

        # Unblock signals:
        self.blockSignals(False)

        # Notify config:
        self.__modified = False
        self.sig_data_modified.emit(self.__node, self.__modified)

    def insert_row(self):

        row = self.rowCount()
        self.insertRow(row)
        for column in range(self.columnCount()):

            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if column == 0:
                item.setIcon(QIcon("rss/icons/parameter.png"))
                item.setText(QSS.random_id(length = 4, prefix = "L#"))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            if column == 2:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            if column == 10:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            if 5 <= column < 9:
                item.setBackground(QColor(0xF6F0DF))

            self.setItem(row, column, item)

        return row

    def delete_row(self):

        # Get selected rows
        indices = self.selectedIndexes()
        row_set = set()
        col_set = set()
        for index in indices:
            row_set.add(index.row())
            col_set.add(index.column())

        # Only delete if the entire row was selected:
        if len(col_set) != self.columnCount():
            print(f"Select all columns and try again")
            return

        # First sort the rows in descending order:
        row_set = sorted(row_set, reverse=True)
        for row in row_set:
            uid = self.item(row, 0)
            sym = self.item(row, 1)

            if sym and self.__eqwidget:
                self.__eqwidget.delete_symbols(sym.text())
                self.__eqwidget.update()

            if uid is None or not uid.text().startswith('H'):
                self.removeRow(row)

    def on_insert_row(self):
        self.insert_row()
        self.__modified = True
        self.sig_data_modified.emit(self.__node, self.__modified)

    def on_delete_row(self):
        self.delete_row()
        self.__modified = True
        self.sig_data_modified.emit(self.__node, self.__modified)

    def create_var(self, handle: Handle):

        inp_icon = QIcon("rss/icons/variable.png")
        out_icon = QIcon("rss/icons/output.svg")
        tar_icon = inp_icon if handle.stream() == Stream.INP else out_icon
        color    = QColor(0x98B6B1) if handle.stream() == Stream.INP else QColor(0xffb10a)

        row = self.rowCount() - 1
        print(f"INFO: Sheets.fetch(): {handle.label} with data {handle.value} {handle.lower} {handle.upper} {handle.sigma}")

        self.item(row, 0).setText(handle.id)
        self.item(row, 1).setText(handle.symbol)
        self.item(row, 2).setText(handle.info)
        self.item(row, 3).setText(handle.unit)
        self.item(row, 4).setText(handle.category)
        self.item(row, 5).setText(str(handle.value) if str(handle.value) != "None" else "")
        self.item(row, 6).setText(str(handle.lower) if str(handle.lower) != "None" else "")
        self.item(row, 7).setText(str(handle.upper) if str(handle.upper) != "None" else "")
        self.item(row, 8).setText(str(handle.sigma) if str(handle.sigma) != "None" else "")

        # Customize variable-specific items:
        self.item(row, 0).setBackground(QBrush(color))
        self.item(row, 0).setIcon(tar_icon)

        self.item(row, 0).setFlags(self.item(row, 0).flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.item(row, 1).setFlags(self.item(row, 1).flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.item(row, 4).setFlags(self.item(row, 4).flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.item(row, 9).setFlags(self.item(row, 9).flags() & ~Qt.ItemFlag.ItemIsEditable)

        sym_item = self.item(row, 1)
        sym_item.setFlags(sym_item.flags() | Qt.ItemFlag.ItemIsEditable)

        label_item = self.item(row, 2)
        label_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Numeric fields can be edited:
        for column in range(5, 9):
            item = self.item(row, column)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        # Store handle information in the hash-map:
        self.__hmap[row] = handle

    def create_par(self, parameter: Resource):

        row = self.rowCount() - 1
        self.item(row, 0).setText(parameter.id)
        self.item(row, 1).setText(parameter.symbol)
        self.item(row, 2).setText(parameter.info)
        self.item(row, 3).setText(parameter.unit)
        self.item(row, 4).setText(parameter.category)
        self.item(row, 5).setText(str(parameter.value) if str(parameter.value) != "None" else "")
        self.item(row, 6).setText(str(parameter.lower) if str(parameter.lower) != "None" else "")
        self.item(row, 7).setText(str(parameter.upper) if str(parameter.upper) != "None" else "")
        self.item(row, 8).setText(str(parameter.sigma) if str(parameter.sigma) != "None" else "")

        # Customize variable-specific items:
        self.item(row, 0).setIcon(QIcon("rss/icons/parameter.png"))
        self.item(row, 0).setFlags(self.item(row, 0).flags() & ~Qt.ItemFlag.ItemIsEditable)

        label_item = self.item(row, 2)
        label_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def on_data_changed(self):
        self.sig_data_modified.emit(self.__node, True)
        self.sig_notify_config.emit("Spreadsheet-data modified. There are unsaved changes!")

    def on_copy(self):

        # Empty current clipboard:
        self.__cmap = {}

        # Get indices of copied rows:
        indices = self.selectedIndexes()
        row_set = set()
        col_set = set()
        for index in indices:
            row_set.add(index.row())
            col_set.add(index.column())

        # Abort copy-operation if all columns are not selected.
        if len(col_set) != self.columnCount():
            self.sig_notify_config.emit("ERROR: For copy-paste, all columns must be selected")
            return

        for row in row_set:
            if self.item(row, 1).text().startswith('H'):
                continue

            columns = []
            for j in range(self.columnCount()):
                columns.append(self.item(row, j).clone())

            self.__cmap[row] = columns

    def on_paste(self):

        for row in self.__cmap.keys():
            new_row = self.insert_row()
            columns = self.__cmap[row]
            for j in range(self.columnCount()):
                if j:
                    self.setItem(new_row, j, columns[j].clone())

        self.__modified = True
        self.sig_data_modified.emit(self.__node, self.__modified)

    def validate(self, symlist: dict):

        valid_equations = []
        valid_flag      = False

        for equation in symlist.keys():

            is_valid = True
            symbols  = symlist[equation]

            for symbol in symbols:
                is_valid &= bool(self.findItems(symbol, Qt.MatchFlag.MatchExactly))

            if is_valid:
                valid_equations.append(equation)
            else:
                self.sig_notify_config.emit(f"Equation: {equation} has invalid symbols")

        self.sig_insert_equations.emit(valid_equations)

    def closeEvent(self, event):

        self.__hmap     = {}          # Clear hash-map
        self.__cmap     = {}          # Clear column-map
        self.__node     = None        # Remove reference (Important to ensure the node is properly deleted)
        self.__modified = False       # Reset the modification state

        # Call base-class implementation:
        super().closeEvent(event)