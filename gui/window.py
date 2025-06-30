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
from custom.dialog import Dialog

from .tabber import Tabber
from .navbar import NavBar

from tabs.optima.optimizer import Optimizer
from tabs.database.manager import DataManager

# The application's main interface
class Gui(QMainWindow):

    # Constructor:
    def __init__(self):
        """
        Instantiates and organizes several child widgets that directly interface with the user. The central widget is a
        QStackWidget that allows the user to switch between the application's main 'pages', including the drawing area
        (canvas), data manager, and optimization setup through a detachable navigation bar (NavBar).
        """

        # Initialize base-class:
        super().__init__(None)

        # Widgets:
        self._navbar = NavBar(self)             # Navigation bar that contains icon-buttons for switching between the main widgets.
        self._wstack = QStackedWidget(self)     # Main Widget #1 - Allows user to switch between different main widgets.
        self._tabber = Tabber(self._wstack)     # Main Widget #2 - Allows the user to create, edit, and manage multiple canvas tabs.

        self._sheets = DataManager(self)   # Main Widget #3 - Allows the user to view and edit schematic data in a tabular format.
        self._optima = Optimizer  (self)   # Main Widget #4 - Allows the user to set up and run constrained optimization problems.

        # Add stack-widgets:
        self._wstack.addWidget(self._tabber)
        self._wstack.addWidget(self._sheets)
        self._wstack.addWidget(self._optima)

        # Add `_navbar` as a toolbar:
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._navbar)
        self.setCentralWidget(self._wstack)

        # Connect navbar's signal:
        self._navbar.sig_open_schema.connect(self._tabber.import_schema)
        self._navbar.sig_save_schema.connect(self._tabber.export_schema)
        self._navbar.sig_show_widget.connect(self.set_active_widget)

        # Connect the canvas's double-clicked signal:
        self._tabber.sig_node_clicked.connect(lambda: self._navbar.select_action("Sheets"))

        # Initialize menu:
        self._init_menubar()
        self.showMaximized()

    # Create a menu-bar and add menu items:
    def _init_menubar(self):

        # Instantiate menu-bar:
        _menu = self.menuBar()
        _menu.setNativeMenuBar(False)       # Menu should appear within the main-window (for macOS)
        _menu.setObjectName("Climact Menu") # Set a unique object name

        _file_menu = _menu.addMenu("File")  # New project, import/export, quit
        _edit_menu = _menu.addMenu("Edit")  # Edit menu
        _view_menu = _menu.addMenu("View")  # View menu
        _help_menu = _menu.addMenu("Help")  # Help menu

        # Add actions and connect them to appropriate slots:
        _newtab_action = _file_menu.addAction("New Tab", self._tabber.create_tab)

        _file_menu.addSeparator()
        _import_action = _file_menu.addAction("Import Schema", QKeySequence.StandardKey.Open, self._tabber.import_schema)
        _export_action = _file_menu.addAction("Export Schema", QKeySequence.StandardKey.Save, self._tabber.export_schema)

        _file_menu.addSeparator()
        _quit_action = _file_menu.addAction("Quit Application", QKeySequence.StandardKey.Quit, QApplication.instance().quit)

    def load_project(self): self._tabber.import_schema()

    def set_active_widget(self, label: str):

        """
        Sets the active widget in the QStackedWidget based on the argument `label` received from the NavBar.
        :param label:
        """
        if  label == "Canvas" and self._wstack.currentWidget() != self._tabber:
            self._wstack.setCurrentWidget(self._tabber)
            return

        if label == "Sheets" and self._wstack.currentWidget() != self._sheets:
            self._sheets.reload(self._tabber.canvas)
            self._wstack.setCurrentWidget(self._sheets)
            return

        if  label == "Optima" and self._wstack.currentWidget() != self._optima:
            self._wstack.setCurrentWidget(self._optima)
            return