#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------
import logging

from PyQt6.QtGui  import QShortcut, QKeySequence
from PyQt6.QtCore import (
    Qt,
    QtMsgType,
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QApplication,
    QStackedWidget
)

from dataclasses   import dataclass
from custom.message import Message

from .tabber import Tabber
from .navbar import NavBar

from tabs.optima.optimizer import Optimizer
from tabs.database.manager import DataManager

# Class Gui:
class Gui(QMainWindow):

    # Signals:
    sig_init_window = pyqtSignal()

    # Default attrib:
    @dataclass(frozen = True, repr = True)
    class Attr:
        title  = "Climact"      # Default title
        width  = 1920           # Default width
        height = 1080           # Default height

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
        self._init_shortcuts()

        self.showMaximized()

    # Create a menu-bar and add menu items:
    def _init_menubar(self):

        # Instantiate menu-bar:
        _menu = self.menuBar()
        _menu.setNativeMenuBar(False)       # The menubar should appear within the main-window (for macOS)
        _menu.setObjectName("Climact Menu") # Set a unique object name

        _file_menu = _menu.addMenu("File")  # New project, import/export, quit
        _edit_menu = _menu.addMenu("Edit")  # Includes undo/redo, copy/paste, etc.
        _view_menu = _menu.addMenu("View")  # Includes find/search, zoom in/out, etc.
        _help_menu = _menu.addMenu("Help")  # Includes about, documentation, etc.

        _file_menu.addSeparator()
        _import_action = _file_menu.addAction("Import Schema", QKeySequence.StandardKey.Open, self._tabber.import_schema)
        _export_action = _file_menu.addAction("Export Schema", QKeySequence.StandardKey.Save, self._tabber.export_schema)

        _file_menu.addSeparator()
        _quit_action = _file_menu.addAction("Quit Application", QKeySequence.StandardKey.Quit, QApplication.instance().quit)

    # Initialize keyboard shortcuts:
    def _init_shortcuts(self):

        # Navigation shortcuts:
        shortcut_up    = QShortcut(QKeySequence.StandardKey.MoveToPreviousLine, self, self._navbar.previous)
        shortcut_left  = QShortcut(QKeySequence.StandardKey.MoveToPreviousChar, self)
        shortcut_down  = QShortcut(QKeySequence.StandardKey.MoveToNextLine, self, self._navbar.next)
        shortcut_right = QShortcut(QKeySequence.StandardKey.MoveToNextChar, self)

        shortcut_left .activated.connect(lambda: self._tabber.setCurrentIndex(self._tabber.currentIndex() - 1))
        shortcut_right.activated.connect(lambda: self._tabber.setCurrentIndex(self._tabber.currentIndex() + 1))

    def load_project(self): self._tabber.import_schema()

    def show_widget(self, _label: str):

        if _label == "Data":
            self._data.reload(self._tabber.currentWidget().canvas)
            self._wstack.setCurrentWidget(self._data)

        if _label == "Optima":
            self._optima.reload(self._tabber.currentWidget().canvas)
            self._wstack.setCurrentWidget(self._optima)


        if _label == "Canvas":      self._wstack.setCurrentWidget(self._tabber)
        if _label == "Assistant":   self._tabber.currentWidget().toggle_assistant()

    def closeEvent(self, event):

        """
        # Confirm quit:
        _dialog = Message(QtMsgType.QtWarningMsg,
                         "Do you want to save unsaved changes?",
                          QMessageBox.StandardButton.Yes |
                          QMessageBox.StandardButton.No |
                          QMessageBox.StandardButton.Cancel
                          )

        # Execute dialog and get result:
        _dialog_code = _dialog.exec()

        # Handle close-event accordingly:
        if _dialog_code == QMessageBox.StandardButton.Yes:      event.accept()
        if _dialog_code == QMessageBox.StandardButton.No:       event.accept()
        if _dialog_code == QMessageBox.StandardButton.Cancel:   event.ignore()
        """
