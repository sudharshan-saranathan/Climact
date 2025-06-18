"""
    climact.window
    --------------
    This module defines the main GUI window for the Climact application. The `Gui` class inherits from `QMainWindow`
    and serves as the main interface for the application. It initializes a central `QStackedWidget` that manages various
    child widgets, including
    - A `QTabWidget` subclass for managing multiple canvases simultaneously.
    - A custom data-manager widget for viewing and editing schematic data.
    - A custom optimization-settings widget to configure and run optimization algorithms.

    To switch between these widgets, the user can interact with a custom navigation bar that visually resembles the
    start-menu of operating systems like Windows or macOS. Apart from this, the `Gui` class also includes a menu bar
    with various actions for file management, editing, viewing, and accessing help documentation, and defines useful
    keyboard shortcuts.
"""

# Debugging:
import logging

# PyQt6.QtGui module:
from PyQt6.QtGui import (
    QShortcut,
    QKeySequence
)

# PyQt6.QtCore module:
from PyQt6.QtCore import Qt

# PyQt6.QtWidgets module:
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QStackedWidget
)

# User-defined modules:
from gui.navbar import NavBar
from gui.tabber import Tabber
from tabs.database.manager import DataManager
from tabs.maps.maps import *

# Class Gui: Main window of the Climact application.
class Gui(QMainWindow):
    """
    A subclass of QMainWindow that serves as the main interface for the Climact application.

    Class Methods:
    --------------
    - init_menubar():
        Initializes the application's menu bar with four main menus - 'File', 'Edit', 'View', and 'Help'.
        Each menu contains various actions such as importing/exporting, creating new widgets, quitting the application,
        zooming, accessing the help documentation, and more.

    - init_shortcuts():
        Defines keyboard shortcuts for navigation and other actions within the application.

    - import_project():
        Opens an interactive dialog for the user to load a previously saved project file. If the file does not exist
        or is invalid, an error message is displayed. Otherwise, the project is loaded into the currently active
        canvas.

    - set_active_widget(_label: str):
        Sets the active widget in the QStackedWidget based on the label received from the NavBar.
        This allows switching between different views such as the tabber, data manager, and optimization settings.
    """

    # Initializer:
    def __init__(self):
        super().__init__(None)  # QMainWindow constructor does not take any parent widget

        # Widgets:
        self._wstack  = QStackedWidget(self)    # This is the central widget of the main window.
        self._tabber = Tabber(self)             # QTabWidget subclass to manage multiple canvases.
        self._navbar = NavBar(self)             # Interactive navigation pane that is set as a toolbar.
        self._charts = QWidget(self)            # Custom widget for plotting graphs and charts.
        self._optima = QWidget(self)            # Custom optimization-settings widget for configuring and running optimization algorithms
        self._sheets = DataManager(
            self._tabber.canvas,
            self
        )

        # Add stack-widgets:
        self._wstack.addWidget(self._tabber)    # The first widget in the stack is the tabber
        self._wstack.addWidget(self._sheets)    # The second widget is the data-manager
        self._wstack.addWidget(self._charts)    # The third widget is the schematic viewer
        self._wstack.addWidget(self._optima)    # The third widget is the optimization-settings

        # Add `self._navbar` as a toolbar and set the central widget:
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self._navbar)
        self.setCentralWidget(self._wstack)

        # The navigation bar emits signals to switch between widgets. Connect these to `self.set_active_widget`:
        self._navbar.sig_open_schema.connect(self._tabber.import_project)
        self._navbar.sig_save_schema.connect(self._tabber.export_project)
        self._navbar.sig_show_widget.connect(self.set_active_widget)

        # Connect the canvas's double-clicked signal:
        self._tabber.canvas.sig_open_database.connect(lambda: self._navbar.select_action("Sheets"))

        self._init_menubar()    # Initialize the menu bar with various actions
        self.showMaximized()    # Show the main window maximized

    # Create a menu-bar and add menu items:
    def _init_menubar(self):

        # Instantiate menu-bar:
        _menu = self.menuBar()
        _menu.setNativeMenuBar(False)           # Menu should appear within the main window (for macOS)

        # Main menus:
        _file_menu = _menu.addMenu("File")      # File menu
        _edit_menu = _menu.addMenu("Edit")      # Edit menu
        _view_menu = _menu.addMenu("View")      # View menu
        _help_menu = _menu.addMenu("Help")      # Help menu

        # File menu:
        _file_menu.addAction("Open Project", QKeySequence.StandardKey.Open, self._tabber.import_project)
        _file_menu.addAction("Save Project", QKeySequence.StandardKey.Save, self._tabber.export_project)
        _file_menu.addSeparator()
        _file_menu.addAction("Export to AMPL")
        _file_menu.addAction("Export to CasADi")
        _file_menu.addSeparator()
        _file_menu.addAction("Quit Application", QKeySequence.StandardKey.Quit, QApplication.instance().quit)

        # Edit menu:
        _edit_menu.addAction("Undo")
        _edit_menu.addAction("Redo")
        _edit_menu.addSeparator()
        _edit_menu.addAction("Clone")
        _edit_menu.addAction("Paste")
        _edit_menu.addSeparator()
        _edit_menu.addAction("Find")
        _edit_menu.addAction("Select All")

        # View menu:
        _view_menu.addAction("Zoom In")
        _view_menu.addAction("Zoom Out")
        _view_menu.addAction("Reset Zoom")

        # Help menu:
        _help_menu.addAction("About")
        _help_menu.addAction("Shortcuts")

    # Import a project:
    def import_project(self):
        """
        Forwards the signal-trigger to the import_project method of the Tabber instance.
        """
        self._tabber.import_project()

    # Set the active widget based on the label received from the NavBar:
    def set_active_widget(self, label: str):
        """
        Sets the active widget in the QStackedWidget based on the argument `label` received from the NavBar.
        :param label:
        """
        if  label == "Canvas" and self._wstack.currentWidget() != self._tabber:
            self._wstack.setCurrentWidget(self._tabber)
            return

        if  label == "Sheets" and self._wstack.currentWidget() != self._sheets:
            self._sheets.reload(self._tabber.canvas)
            self._wstack.setCurrentWidget(self._sheets)
            return 

        if  label == "Optima" and self._wstack.currentWidget() != self._optima:
            self._wstack.setCurrentWidget(self._optima)
            return

        if  label == "Maps" and self._wstack.currentWidget() != self._charts:
            self._wstack.setCurrentWidget(self._charts)
            return