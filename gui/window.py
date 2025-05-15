#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------
import logging

from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal, QtMsgType
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QApplication

from dataclasses   import dataclass
from custom.dialog import Dialog

from .tabber import Tabber
from .navbar import NavBar

from tabs.optima.optimizer import Optimizer
from tabs.database.manager import DataManager
# from tabs.sheets.manager import Manager

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
        self._wstack = QStackedWidget(self)     # Central stacked-widget
        self._tabber = Tabber(self._wstack)     # Tab-widget to hold multiple canvas
        self._navbar = NavBar(self)             # Detachable, interactive navigation-bar

        self._data   = DataManager(self._tabber.currentWidget().canvas, self)
        self._optima = Optimizer  (self._tabber.currentWidget().canvas, self)

        # Add stack-widgets:
        self._wstack.addWidget(self._tabber)    # Tab-widget to hold multiple canvas
        self._wstack.addWidget(self._data)      # Data-manager
        self._wstack.addWidget(self._optima)    # Optimizer

        # Add `_navbar` as a toolbar:
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._navbar)
        self.setCentralWidget(self._wstack)

        # Connect navbar's signal:
        self._navbar.sig_open_schema.connect(self._tabber.import_schema)
        self._navbar.sig_save_schema.connect(self._tabber.export_schema)
        self._navbar.sig_show_widget.connect(self.show_widget)

        # Initialize menu:
        self._init_menubar()
        self.showMaximized()

    # Create menu-bar and menu items:
    def _init_menubar(self):

        # Instantiate menu-bar:
        _menu = self.menuBar()
        _menu.setNativeMenuBar(False)       # Menu should appear within main-window (for macOS)
        _menu.setObjectName("Climact Menu") # Set unique object name

        _file_menu = _menu.addMenu("File")  # New project, import/export, quit
        _edit_menu = _menu.addMenu("Edit")  # Edit menu
        _view_menu = _menu.addMenu("View")  # View menu
        _help_menu = _menu.addMenu("Help")  # Help menu

        # Add actions and connect them to appropriate slots:
        _newtab_action = _file_menu.addAction("New Tab", QKeySequence("Ctrl+T"))

        _file_menu.addSeparator()
        _import_action = _file_menu.addAction("Import Schema", QKeySequence.StandardKey.Open)
        _export_action = _file_menu.addAction("Export Schema", QKeySequence.StandardKey.Save)

        _file_menu.addSeparator()
        _quit_action = _file_menu.addAction("Quit Application", QKeySequence.StandardKey.Quit)

        _newtab_action.triggered.connect(self._tabber.addTab)
        _import_action.triggered.connect(self._tabber.import_schema)
        _export_action.triggered.connect(self._tabber.export_schema)
        _quit_action.triggered.connect(QApplication.instance().quit)

    def load_project(self): self._tabber.import_schema()

    def show_widget(self, _label: str):

        if _label == "Data":
            self._data.reload(self._tabber.currentWidget().canvas)
            self._wstack.setCurrentWidget(self._data)

        if _label == "Canvas":      self._wstack.setCurrentWidget(self._tabber)
        if _label == "Optima":      self._wstack.setCurrentWidget(self._optima)
        if _label == "Assistant":   self._tabber.currentWidget().toggle_assistant()

    def closeEvent(self, event):

        # Confirm quit:
        _dialog = Dialog(QtMsgType.QtWarningMsg,
                         "Do you want to save unsaved changes?",
                         QMessageBox.StandardButton.Yes     |
                         QMessageBox.StandardButton.No |
                         QMessageBox.StandardButton.Cancel
                         )

        # Execute dialog and get result:
        _dialog_code = _dialog.exec()

        # Handle close-event accordingly:
        if _dialog_code == QMessageBox.StandardButton.Yes:
            event.accept()

        if _dialog_code == QMessageBox.StandardButton.No:       event.accept()
        if _dialog_code == QMessageBox.StandardButton.Cancel:   event.ignore()