#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# Year      : 2025
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1)

from PyQt6.QtGui     import QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal, QtMsgType
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QStatusBar, QApplication, QWidget

from dataclasses    import dataclass
from core.dialog    import Dialog
from tabs.optima import Optimizer
from tabs.schema.viewer import Viewer
from gui.navbar     import NavBar
from tabs.sheets.manager import Manager


#-----------------------------------------------------------------------------------------------------------------------

class Gui(QMainWindow):

    # Signals:
    sig_init_window = pyqtSignal()

    # Default attrib:
    @dataclass(frozen=True, slots=True)
    class Attr:
        title  = "CLIMACT"
        width  = 1920       # Default width
        height = 1080       # Default height

    # Initializer:
    def __init__(self):

        # Initialize base-class:
        super().__init__(None)

        # Widgets:
        self._navbar = NavBar(self)             # Detachable toolbar
        self._viewer = Viewer(self)             # QGraphicsView subclass
        self._status = QStatusBar(self)         # Window-level status bar
        self._wstack = QStackedWidget(self)     # Container for other child-widgets:
        self._optima = Optimizer(self._viewer.canvas, self._wstack)
        self._sheets = Manager(self._viewer.canvas, self)

        # Set NavBar instance as a toolbar:
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._navbar)
        self.setCentralWidget(self._wstack)
        self.setStatusBar(self._status)

        # Connect navbar's signal:
        self._navbar.sig_show_widget.connect(self.set_stacked_widget)

        # Organize stack-widget:
        self._wstack.addWidget(self._viewer)
        self._wstack.addWidget(self._sheets)
        self._wstack.addWidget(self._optima)

        # Initialize menu:
        self.__menu__()
        self.showMaximized()

    def __menu__(self):

        _menu = self.menuBar()
        _menu.setNativeMenuBar(False)       # Menu appears within the main-window (especially for macOS)
        _menu.setObjectName("Climact Menu")

        _file_menu = _menu.addMenu("File")
        _edit_menu = _menu.addMenu("Edit")
        _view_menu = _menu.addMenu("View")
        _help_menu = _menu.addMenu("Help")

        _window_action = _file_menu.addAction("New Project", QKeySequence.StandardKey.New)
        _window_action.triggered.connect(self.sig_init_window.emit)

        _file_menu.addSeparator()
        _import_action = _file_menu.addAction("Import Schema", QKeySequence.StandardKey.Open)
        _import_action.triggered.connect(lambda: print("Importing schema"))

        _export_action = _file_menu.addAction("Export Schema", QKeySequence.StandardKey.Open)
        _export_action.triggered.connect(lambda: print("Exporting schema"))

        _file_menu.addSeparator()
        _quit_action = _file_menu.addAction("Quit Application", QKeySequence.StandardKey.Quit)
        _quit_action.triggered.connect(lambda: QApplication.instance().quit())

    def set_stacked_widget(self, name: str):

        if not isinstance(name, str):
            return

        if name == "Canvas":
            self._wstack.setCurrentWidget(self._viewer)

        if name == "Sheets":
            self._sheets.reload()
            self._wstack.setCurrentWidget(self._sheets)

        if name == "Optimization":
            self._wstack.setCurrentWidget(self._optima)

        if name == "Assistant":
            self._viewer.toggle_assistant()

    def closeEvent(self, event):

        # Confirm quit:
        _dialog = Dialog(QtMsgType.QtWarningMsg,
                         "Do you want to save unsaved changes?",
                         QMessageBox.StandardButton.Yes     |
                         QMessageBox.StandardButton.No |
                         QMessageBox.StandardButton.Cancel
                         )

        if _dialog.exec() == QMessageBox.StandardButton.Cancel:
            event.ignore()

        else:
            event.accept()

