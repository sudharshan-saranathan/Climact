
# Debugging:
import logging
import qtawesome as qta

# PyQt6.QtGui module:
from PyQt6.QtGui     import (
    QIcon,
    QAction,
    QActionGroup
)

# PyQt6.QtCore module:
from PyQt6.QtCore    import (
    Qt,
    QSize,
    pyqtSignal
)

# PyQt6.QtWidgets module:
from PyQt6.QtWidgets import (
    QWidget,
    QToolBar,
    QMessageBox,
    QApplication
)

# Class NavBar: A vertical navigation bar for the Climact application.
class NavBar(QToolBar):
    """
    This class inherits from QToolBar and serves as a vertical navigation bar for the Climact application.

    Class Methods:
    --------------
    - select_next():
        Triggers the next action in the navigation bar, cycling through the available actions.

    - select_prev():
        Triggers the previous action in the navigation bar, cycling through the available actions.
    """

    # Signals:
    sig_open_schema = pyqtSignal()      # Emitted when the user clicks the "Open" action
    sig_save_schema = pyqtSignal()      # Emitted when the user clicks the "Save" action
    sig_show_widget = pyqtSignal(str)   # Emitted when the user clicks one of the actions in the navbar

    # Initializer:
    def __init__(self,
                 parent: QWidget | None,
                 **kwargs):

        # Initialize base-class:
        super().__init__(parent)
        super().setIconSize(QSize(32, 32))
        super().setOrientation(Qt.Orientation.Vertical)

        # Define new actions and add them to the toolbar:
        self._import_schematic = self.addAction(QIcon("rss/icons/json.png")   , "Open", self.sig_open_schema.emit)
        self._export_schematic = self.addAction(QIcon("rss/icons/floppy.png") , "Save", self.sig_save_schema.emit)
        self._switch_to_canvas = self.addAction(QIcon("rss/icons/hammer.png") , "Canvas", lambda: self.sig_show_widget.emit(self._switch_to_canvas.text()))
        self._switch_to_sheets = self.addAction(QIcon("rss/icons/sheets.png") , "Sheets", lambda: self.sig_show_widget.emit(self._switch_to_sheets.text()))
        self._switch_to_script = self.addAction(QIcon("rss/icons/charts.png") , "Charts", lambda: self.sig_show_widget.emit(self._switch_to_script.text()))
        self._switch_to_optima = self.addAction(QIcon("rss/icons/python.png") , "Optima", lambda: self.sig_show_widget.emit(self._switch_to_optima.text()))
        self._toggle_assistant = self.addAction(QIcon("rss/icons/assist.png") , "Assist", lambda: self.sig_show_widget.emit(self._toggle_assistant.text()))
        self._template_library = self.addAction(QIcon("rss/icons/library.png"), "Library")

        # Save actions in a list for easy access:
        self._actions = [
            self._switch_to_canvas,
            self._switch_to_sheets,
            self._switch_to_script,
            self._switch_to_optima,
        ]

        # Make canvas, sheets, script, and config checkable:
        self._switch_to_canvas.setCheckable(True)
        self._switch_to_sheets.setCheckable(True)
        self._switch_to_script.setCheckable(True)
        self._switch_to_optima.setCheckable(True)
        self._toggle_assistant.setCheckable(True)
        self._template_library.setCheckable(True)
        self._switch_to_canvas.setChecked(True)

        # Create an action group and toggle exclusivity:
        _action_group = QActionGroup(self)
        _action_group.addAction(self._switch_to_canvas)
        _action_group.addAction(self._switch_to_sheets)
        _action_group.addAction(self._switch_to_script)
        _action_group.addAction(self._switch_to_optima)
        _action_group.setExclusive(True)

    # Activate the next action in the navbar:
    def select_next(self):
        """
        Triggers the next action in the navbar.
        """

        # Find the currently checked action and trigger the next in cycle:
        if  checked_action := next((action for action in self._actions if action.isChecked()), None):
            checked_index = self._actions.index(checked_action)
            self._actions[(checked_index + 1) % len(self._actions)].trigger()

    # Activate the previous action in the navbar:
    def select_prev(self):
        """
        Triggers the prev action in the navbar.
        """

        # Find the currently checked action and trigger the previous in cycle:
        if  checked_action := next((action for action in self._actions if action.isChecked()), None):
            checked_index = self._actions.index(checked_action)
            self._actions[(checked_index - 1) % len(self._actions)].trigger()

    # Activate a specific action by name:
    def select_action(self, action_name: str):
        """
        Activates a specific action by its name.

        Parameters:
            action_name (str): The name of the action to activate.
        """
        for action in self._actions:
            if action.text() == action_name:
                action.trigger()
                return

        logging.warning(f"Action '{action_name}' not found in the navigation bar.")