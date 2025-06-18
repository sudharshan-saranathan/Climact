"""
    climact.tabber
    --------------
    This module defines a custom QTabWidget subclass for managing multiple Viewer tabs in the Climact application.
    The `Tabber` class provides functionality to create, remove, and rename tabs, as well as import and export projects.
    It also includes a context menu for tab management and keyboard shortcuts for quick access to various actions.
    The `Tabber` class is designed to handle up to a maximum of 8 tabs, each containing a `Viewer` widget for displaying
    and interacting with graphical content.
"""

__author__ = "Sudharshan Saranathan"
__version__ = "0.1.0"
__license__ = "None"
__date__ = "2025-05-26"

# Standard library imports:
import os
import logging

from pathlib import Path


# PyQt6 library (pip install PyQt6:
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QShortcut,
    QKeySequence
)
from PyQt6.QtWidgets import (
    QMenu,
    QWidget,
    QCheckBox,
    QTabWidget,
    QFileDialog,
    QApplication
)

# QtAwesome (for fonts and icons):
import qtawesome as qta

# Climact sub-modules:
from custom.getter import Getter
from custom.message import Message
from tabs.schema.viewer import Viewer

# Class Tabber: A custom QTabWidget for managing multiple Viewer tabs.
class Tabber(QTabWidget):
    """
    This class inherits from QTabWidget and provides functionality to switch between different widgets.

    Class Methods:
    --------------
    - contextMenuEvent():
        Creates a context menu when the user right-clicks on a tab, allowing them to rename or delete the tab.

    - create_tab():
        Creates a new tab with a Viewer widget and sets it as the current tab.

    - remove_tab():
        Removes a tab at the specified index.

    - rename_tab():
        Renames the tab at the specified index with a new name provided by the user.
    """

    # Constants for the Tabber class:
    MAX_TABS = 8

    # Initializer:
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Define corner-widget:
        check = QCheckBox("Save", self)
        check.setChecked(True)

        # Customize attributes:
        self.index = -1
        self.create_tab()
        self.setTabsClosable(True)
        self.setCornerWidget(check)
        self.setTabShape(QTabWidget.TabShape.Rounded)

        # Initialize the context menu:
        self._init_menu()
        self._init_keys()

        # Connect signals to slots:
        self.tabCloseRequested.connect(self.remove_tab)

    # Method to initialize the context menu:
    def _init_menu(self):

        # Create a context-menu:
        self._menu  = QMenu(self)

        # Context-menu actions:
        create = self._menu.addAction(qta.icon('mdi.tab-plus', color='green'),
                                      "New Tab", QKeySequence("Ctrl+T"),
                                      self.create_tab)

        rename = self._menu.addAction(qta.icon('fa5s.pen', color='darkgray'),
                                      "Rename", QKeySequence("Ctrl+R"),
                                      lambda: self.rename_tab(self.index))

        delete = self._menu.addAction(qta.icon('fa5s.trash', color='red'),
                                      "Delete", QKeySequence("Ctrl+W"),
                                      lambda: self.remove_tab(self.index))

        create.setIconVisibleInMenu(True)
        rename.setIconVisibleInMenu(True)
        delete.setIconVisibleInMenu(True)

        create.setShortcutVisibleInContextMenu(True)
        rename.setShortcutVisibleInContextMenu(True)
        delete.setShortcutVisibleInContextMenu(True)

    # Method to initialize keyboard shortcuts:
    def _init_keys(self):
        """
        Initializes keyboard shortcuts for the tab widget.
        """

        # Shortcuts to create and close tabs:
        self._create_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self, self.create_tab)
        self._rename_tab_shortcut = QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.rename_tab(self.currentIndex()))
        self._delete_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.remove_tab(self.currentIndex()))

        # Shortcuts to switch between tabs using Ctrl+1, Ctrl+2, ..., Ctrl+8:
        for j in range(self.MAX_TABS):
            QShortcut(
                QKeySequence(f"Ctrl+{j + 1}"),
                self, lambda index=j: self.setCurrentIndex(index)
            )

    # Context-menu event handler:
    def contextMenuEvent(self, event):
        """
        Event-handler for the context menu event, triggered when the user right-clicks on a tab.
        :param event: The context menu event (instantiated and managed by Qt).
        """

        # Show the context menu at the position of the clicked tab:
        self.index = self.tabBar().tabAt(event.pos())

        if  self.index < 0:
            QApplication.beep()
            return

        # Show context-menu:
        self._menu.exec(event.globalPos())

    # Method to create a new tab:
    def create_tab(self):
        """
        Creates a new Viewer and adds it as a tab.
        """
        if self.count() >= self.MAX_TABS:
            QApplication.beep()
            return

        # Create a new tab and set as current:
        self.addTab(viewer := Viewer(self), f"Untitled_{self.count() + 1}*")
        self.setCurrentWidget(viewer)

        # Rename the tab to the filename when the project is loaded:
        viewer.canvas.sig_loaded_project.connect(lambda filename: self.setTabText(self.currentIndex(),filename + "*"))

    # Method to close and remove a tab:
    def remove_tab(self, index: int):
        """
        This method removes the tab at the specified index, then deletes the associated widget.

        :param: index: The index of the tab to remove.
        """
        if index < 0 or index >= self.count():
            QApplication.beep()
            return

        # Delete the widget:
        widget = self.widget(index)
        widget.close()
        widget.deleteLater()

        # Call super-class implementation:
        self.removeTab(index)

    # Method to rename a tab:
    def rename_tab(self, index: int | None = None):
        """
        Renames the tab at the specified index with a new name provided by the user.
        :param: index: The index of the tab to rename.
        """

        # If no index is provided, use the current index:
        if  index is None:
            index = self.index

        # Create a new Getter dialog to get the new label:
        usr_input = Getter("New Label", "Name", self, Qt.WindowType.Popup)
        usr_input.open()

        # Get current suffix:
        suffix = "*" if self.tabText(index).endswith("*") else ""

        # Connect the finished signal to set the tab text:
        usr_input.finished.connect(
            lambda: self.setTabText(
                index,
                usr_input.text() + suffix
            ) if usr_input.result() and usr_input.text() else None
        )

    # Import a new project into the current canvas:
    def import_project(self, project: str = ""):
        """
        Imports a new project into the viewer.

        :param project: The path to the project file to be imported.
        :param clear: If True, the canvas is cleared before importing the project.
        """
        # Get the current widget and import the project:
        if  self.canvas:
            self.canvas.import_project(project)

        else:
            logging.critical("The current widget is not a Viewer instance. Cannot import project!")
            Message.critical(self,
                             "Invalid Viewer",
                             "The current widget is not a Viewer instance. Cannot import project!")

    # Export the current project:
    def export_project(self):
        """
        Exports the currently visible schematic as a JSON file.
        """
        # Get the current tab-label, strip any trailing asterisk:
        filename = self.tabText(self.currentIndex()).rstrip("*") + ".json"

        # If the corner widget is not checked, get a filename from the user:
        if  not self.cornerWidget().isChecked():
            filename, _ = QFileDialog.getSaveFileName(self,
                                                      "Export Project", os.getcwd(),
                                                      "Climact Project Files (*.json);;All Files (*)")

        # If the filename is empty, return:
        if  not filename:
            logging.info("No filename provided for export.")
            return

        # Export the project to the specified filename:
        self.currentWidget().canvas.export_project(filename)
        self.setTabText(self.currentIndex(), Path(filename).stem)

    #
    #
    #

    @property
    def canvas(self):
        """
        Returns the current canvas associated with the active tab.
        :return:
        """
        viewer = self.currentWidget()
        if  isinstance(viewer, Viewer):
            return viewer.canvas

        return None




