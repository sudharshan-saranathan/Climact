#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact.git
# File      : tabber.py
# Created   : 2025-05-26
# Purpose   : Custom QTabWidget for managing multiple QGraphicsView tabs in the Climact application.
#-----------------------------------------------------------------------------------------------------------------------

# QtAwesome (pip install qtawesome):
import qtawesome as qta

# PyQt6.QtGui module:
from PyQt6.QtGui import (
    QShortcut,
    QKeySequence
)

# PyQt6.QtCore module:
from PyQt6.QtCore import (
    Qt
)

# PyQt6.QtWidgets module:
from PyQt6.QtWidgets import (
    QMenu,
    QWidget,
    QCheckBox,
    QTabWidget,
    QFileDialog,
    QMessageBox,
    QApplication
)

from custom.getter  import Getter
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
    class Constants:
        MAX_TABS = 8

    # Initializer:
    def __init__(self, parent: QWidget | None = None):

        # Initialize super-class:
        super().__init__(parent)

        # Initialize context-menu index:
        self._menu_index = -1

        # Define corner-widget:
        check = QCheckBox("Save", self)
        check.setChecked(True)

        # Customize attributes:
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
        self._menu = QMenu(self)
        rename = self._menu.addAction(qta.icon('fa5s.pen'  , color='darkgray'), "Rename", lambda: self.rename_tab(self._menu_index))
        delete = self._menu.addAction(qta.icon('fa5s.trash', color='darkred') , "Delete", lambda: self.remove_tab(self._menu_index))

        rename.setIconVisibleInMenu(True)
        delete.setIconVisibleInMenu(True)

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
        for j in range(self.Constants.MAX_TABS):
            QShortcut(
                QKeySequence(f"Ctrl+{j+1}"),
                self, lambda index=j: self.setCurrentIndex(index)
            )

    # Context-menu event handler:
    def contextMenuEvent(self, event):
        """
        This method is called when the user right-clicks on a tab.
        It shows the context menu with options to rename or delete the tab.

        :param event: The context menu event (instantiated and managed by Qt).
        """

        # Show the context menu at the position of the clicked tab:
        self._menu_index = self.tabBar().tabAt(event.pos())
        if self._menu_index == -1:
            QApplication.beep()
            return

        # Show context-menu:
        self._menu.exec(event.globalPos())

    # Method to create a new tab:
    def create_tab(self):
        """
        Creates a new Viewer and adds it as a tab.
        """
        if self.count() >= self.Constants.MAX_TABS:
            QApplication.beep()
            return

        # Create a new tab and set as current:
        self.addTab(viewer := Viewer(self), f"Untitled_{self.count() + 1}*")
        self.setCurrentWidget(viewer)

    # Method to close and remove a tab:
    def remove_tab(self, index: int):
        """
        This method removes the tab at the specified index, then deletes the associated widget.

        :param: index: The index of the tab to remove.
        """
        if  index < 0 or index >= self.count():
            QApplication.beep()
            return

        # Delete the widget:
        widget = self.widget(index)
        widget.close()
        widget.deleteLater()

        # Call super-class implementation:
        self.removeTab(index)

    # Method to rename a tab:
    def rename_tab(self, index: int):
        """
        Renames the tab at the specified index.

        :param: index: The index of the tab to rename.
        """

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
    def import_schema(self, project: str = str(), clear: bool = False) -> None:
        """
        Imports a new project into the viewer.

        :param project: The path to the project file to be imported.
        :param clear: If True, clears the current canvas before importing.
        """

        if not bool(project):
            project, _ = QFileDialog.getOpenFileName(
                self,
                "Import Project",
                "",
                "Climact Project Files (*.json);;All Files (*)"
            )

        # Get the current widget and import the project:
        viewer = self.currentWidget()
        if  viewer:
            viewer.canvas.import_schema(project)

    # Export the current project:
    def export_schema(self):

        # The default filename is the tab-label:
        filename = self.tabText(self.currentIndex()).rstrip("*")

        # But if the corner widget is not checked, get a filename from the user:
        if  not self.cornerWidget().isChecked():
            filename, result = QFileDialog.getSaveFileName(
                self,
                "Export Project",
                "",
                "Climact Project Files (*.json);;All Files (*)"
            )

        if  filename:
            self.currentWidget().canvas.export_schema(filename + ".json")
            self.setTabText(self.currentIndex(), filename)