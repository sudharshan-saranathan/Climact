from PyQt6.QtGui import QIcon, QActionGroup, QAction
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets    import QWidget, QToolBar

class NavBar(QToolBar):

    # Signals:
    sig_open_schema = pyqtSignal()
    sig_save_schema = pyqtSignal()
    sig_show_widget = pyqtSignal(str)

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Adjust width:
        self.setIconSize(QSize(40, 40))
        self.setOrientation(Qt.Orientation.Vertical)

        # Actions:
        self._import_schematic = self.addAction(QIcon("rss/icons/folder.png"), "Open")
        self._export_schematic = self.addAction(QIcon("rss/icons/floppy.png"), "Save")
        self._switch_to_canvas = self.addAction(QIcon("rss/icons/canvas.png"), "Canvas")
        self._switch_to_sheets = self.addAction(QIcon("rss/icons/sheets.png"), "Sheets")
        self._switch_to_script = self.addAction(QIcon("rss/icons/script.png"), "Script")
        self._switch_to_optima = self.addAction(QIcon("rss/icons/python.png"), "Optimization")
        self._toggle_assistant = self.addAction(QIcon("rss/icons/assistant.png"), "Assistant")
        self._template_library = self.addAction(QIcon("rss/icons/components.png"), "Library")

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
        self._init_connections()

    def _init_connections(self):

        self._switch_to_canvas.triggered.connect(self.on_page_selected)
        self._switch_to_sheets.triggered.connect(self.on_page_selected)
        self._switch_to_optima.triggered.connect(self.on_page_selected)
        self._toggle_assistant.triggered.connect(self.on_page_selected)


    def on_page_selected(self):

        action = self.sender()
        if not isinstance(action, QAction):
            return

        self.sig_show_widget.emit(action.text())


