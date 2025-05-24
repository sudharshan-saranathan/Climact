#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------

from PyQt6.QtGui     import QIcon, QActionGroup, QAction
from PyQt6.QtCore    import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QWidget, QToolBar

class NavBar(QToolBar):

    # Signals:
    sig_open_schema = pyqtSignal()      # Emitted when the user clicks the "Open" action
    sig_save_schema = pyqtSignal()      # Emitted when the user clicks the "Save" action
    sig_show_widget = pyqtSignal(str)   # Emitted when the user clicks one of the icons in the navbar

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # Adjust width:
        self.setIconSize(QSize(40, 40))
        self.setOrientation(Qt.Orientation.Vertical)

        # Actions:
        self._import_schematic = self.addAction(QIcon("rss/icons/folder.png"), "Open")          # Action for importing a schematic from a JSON file
        self._export_schematic = self.addAction(QIcon("rss/icons/floppy.png"), "Save")          # Action for saving a schematic to a JSON file
        self._switch_to_canvas = self.addAction(QIcon("rss/icons/canvas.png"), "Canvas")        # Action for switching to the canvas tab
        self._switch_to_sheets = self.addAction(QIcon("rss/icons/sheets.png"), "Data")          # Action for switching to the data tab
        self._switch_to_script = self.addAction(QIcon("rss/icons/script.png"), "Script")        # Action for switching to the script tab
        self._switch_to_optima = self.addAction(QIcon("rss/icons/python.png"), "Optima")        # Action for switching to the optimization tab
        self._toggle_assistant = self.addAction(QIcon("rss/icons/assistant.png"), "Assistant")  # Action for toggling the AI-assistant on and off
        self._template_library = self.addAction(QIcon("rss/icons/components.png"), "Library")   # Action for opening the template library

        # Make canvas, sheets, script, and config checkable:
        self._switch_to_canvas.setCheckable(True)
        self._switch_to_sheets.setCheckable(True)
        self._switch_to_script.setCheckable(True)
        self._switch_to_optima.setCheckable(True)
        self._toggle_assistant.setCheckable(True)
        self._template_library.setCheckable(True)
        self._switch_to_canvas.setChecked(True)

        # Create action group and toggle exclusivity:
        _action_group = QActionGroup(self)
        _action_group.addAction(self._switch_to_canvas)
        _action_group.addAction(self._switch_to_sheets)
        _action_group.addAction(self._switch_to_script)
        _action_group.addAction(self._switch_to_optima)
        _action_group.setExclusive(True)

        # Connect action-signals:
        self._import_schematic.triggered.connect(lambda: self.sig_open_schema.emit())
        self._export_schematic.triggered.connect(lambda: self.sig_save_schema.emit())
        self._switch_to_canvas.triggered.connect(lambda: self.sig_show_widget.emit(self._switch_to_canvas.text()))
        self._switch_to_sheets.triggered.connect(lambda: self.sig_show_widget.emit(self._switch_to_sheets.text()))
        self._switch_to_optima.triggered.connect(lambda: self.sig_show_widget.emit(self._switch_to_optima.text()))
        self._toggle_assistant.triggered.connect(lambda: self.sig_show_widget.emit(self._toggle_assistant.text()))

