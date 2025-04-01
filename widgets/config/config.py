from widgets.schema.graph.handle import *

from .editor import Editor
from .eqlist import Eqlist
from .sheets import Sheets
from .trview import Trview

class Config(QWidget):

    # Initializer:
    def __init__(self, canvas, parent: QWidget = None):

        # Initialize base-class:
        super().__init__(parent)

        # QGraphicsScene:
        self.__canvas = canvas

        # Splitter:
        self.__split  = QSplitter(Qt.Orientation.Horizontal)

        # Layout:
        __grid_layout = QGridLayout(self)
        __grid_layout.setSpacing(0)
        __grid_layout.setContentsMargins(0, 0, 0, 0)
        __grid_layout.setRowStretch(0, 1)
        __grid_layout.setColumnStretch(1, 10)

        # Main widgets:
        self.__eqlist = Eqlist()
        self.__editor = Editor(self)
        self.__trview = Trview(self.__canvas)
        self.__sheets = Sheets(self,self.__eqlist, columns=11,
                               headers=  ['ID', 'Symbol', 'Description', 'Unit', 'Type', 'Value',
                                          'Lower', 'Upper', 'Sigma', 'Interpolate', 'Auto'
                                         ])

        self.__editor.setEnabled(False)
        self.__status = QStatusBar(None)
        self.__status.setFixedHeight(28)

        self.__hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.__hsplit.addWidget(self.__editor)
        self.__hsplit.addWidget(self.__eqlist)
        self.__hsplit.setMinimumHeight(250)
        self.__editor.setPlaceholderText("1. Enter equations in residual form\n"
                                        "2. Enter one equation per line \n"
                                        "3. Press <Enter> to start a new line\n"
                                        "4. Press <Alt+Enter> to save equations\n")

        # Layout:
        __grid_layout.addWidget(self.__trview, 0, 0, 3, 1)
        __grid_layout.addWidget(self.__sheets, 0, 1)
        __grid_layout.addWidget(self.__hsplit, 1, 1, Qt.AlignmentFlag.AlignBottom)
        __grid_layout.addWidget(self.__status, 2, 1, Qt.AlignmentFlag.AlignBottom)

        # Connect signals to event-handlers:
        self.__trview.itemSelectionChanged.connect(self.on_item_selected)
        self.__editor.sig_validate_symbols.connect(self.__sheets.validate)
        self.__sheets.sig_insert_equations.connect(self.__eqlist.insert_equations)

        self.__trview.sig_notify_config.connect(self.__status.showMessage)
        self.__sheets.sig_notify_config.connect(self.__status.showMessage)
        self.__editor.sig_notify_config.connect(self.__status.showMessage)
        self.__eqlist.sig_notify_config.connect(self.__status.showMessage)
        self.__sheets.sig_data_modified.connect(self.__trview.update_icon)

        # Define shortcuts:
        focus_trview = QShortcut(QKeySequence("Ctrl+1"), self)
        focus_sheets = QShortcut(QKeySequence("Ctrl+2"), self)
        focus_editor = QShortcut(QKeySequence("Ctrl+3"), self)
        focus_eqlist = QShortcut(QKeySequence("Ctrl+4"), self)
        sheet_commit = QShortcut(QKeySequence("Ctrl+Return"), self)

        focus_trview.activated.connect(lambda: self.__trview.setFocus(Qt.FocusReason.OtherFocusReason))
        focus_sheets.activated.connect(lambda: self.__sheets.setFocus(Qt.FocusReason.OtherFocusReason))
        focus_editor.activated.connect(lambda: self.__editor.setFocus(Qt.FocusReason.OtherFocusReason))
        focus_eqlist.activated.connect(lambda: self.__eqlist.setFocus(Qt.FocusReason.OtherFocusReason))
        sheet_commit.activated.connect(self.__sheets.commit)

    # Event-handler to display node data:
    @pyqtSlot(name="Fetch and display data")
    def on_item_selected(self):

        item = self.__trview.selectedItems()
        if not len(item):
            return

        self.__editor.setEnabled(True)
        self.__eqlist.setEnabled(True)

        nuid = item[0].text(0).split(':')[0]
        node = self.__canvas.find_by_nuid(nuid)

        if node:
            self.__sheets.fetch(node)                    # Fetch data for the new node

    def showEvent(self, a0):
        self.__trview.refresh()
        super().showEvent(a0)

    def closeEvent(self, a0):

        # Clear the spreadsheet, use QTableWidget.setRowCount(0) instead of QTableWidget.clearContents()
        self.__sheets.setRowCount(0)
        super().closeEvent(a0)
