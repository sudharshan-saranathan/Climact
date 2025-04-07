#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# Year      : 2025
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1)

from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QIcon, QActionGroup, QKeySequence
from PyQt6.QtCore    import QSize
from PyQt6.QtWidgets import QMainWindow, QWidget, QToolBar, QStackedWidget

from widgets.optimize   import Optimizer
from widgets.schema     import Viewer
from widgets.schema     import Config
from dataclasses        import dataclass

#-----------------------------------------------------------------------------------------------------------------------
# Navigator:
class NavBar(QToolBar):

    # Initializer:
    def __init__(self, default_parent: QWidget | None):

        # Initialize base-class:
        super().__init__(default_parent)

        # Adjust width:
        self.setIconSize(QSize(40, 40))
        self.setOrientation(Qt.Orientation.Vertical)

        # Actions:
        self.__load_schematic   = self.addAction(QIcon("rss/icons/folder.png"), "Open")
        self.__save_schematic   = self.addAction(QIcon("rss/icons/floppy.png"), "Save")
        self.__switch_to_canvas = self.addAction(QIcon("rss/icons/canvas.png"), "Canvas")
        self.__switch_to_sheets = self.addAction(QIcon("rss/icons/sheets.png"), "Sheets")
        self.__switch_to_script = self.addAction(QIcon("rss/icons/script.png"), "Script")
        self.__switch_to_optima = self.addAction(QIcon("rss/icons/python.png"), "Optimization")
        self.__switch_to_assist = self.addAction(QIcon("rss/icons/assistant.png"), "Assistant")
        self.__template_library = self.addAction(QIcon("rss/icons/components.png"), "Library")

        # Make canvas, sheets, script, and config checkable:
        self.__switch_to_canvas.setCheckable(True)
        self.__switch_to_sheets.setCheckable(True)
        self.__switch_to_script.setCheckable(True)
        self.__switch_to_optima.setCheckable(True)
        self.__switch_to_assist.setCheckable(True)
        self.__template_library.setCheckable(True)
        self.__switch_to_canvas.setChecked(True)

        # Make a group, toggle exclusivity:
        __action_group = QActionGroup(self)
        __action_group.addAction(self.__switch_to_canvas)
        __action_group.addAction(self.__switch_to_sheets)
        __action_group.addAction(self.__switch_to_script)
        __action_group.addAction(self.__switch_to_optima)
        __action_group.setExclusive(True)

    @property
    def button_open(self):
        return self.__load_schematic

    @property
    def button_save(self):
        return self.__save_schematic

    @property
    def button_canvas(self):
        return self.__switch_to_canvas

    @property
    def button_sheets(self):
        return self.__switch_to_sheets

    @property
    def button_script(self):
        return self.__switch_to_script

    @property
    def button_optima(self):
        return self.__switch_to_optima

    @property
    def button_assist(self):
        return self.__switch_to_assist

    @property
    def button_library(self):
        return self.__template_library

class Gui(QMainWindow):

    # Default attribute(s):
    @dataclass(frozen=True, slots=True)
    class Attr:
        default_title  = "CLIMACT"
        default_width  = 1920        # Default width
        default_height = 1080        # Default height

    # Initializer:
    def __init__(self):

        # Initialize base-class:
        super().__init__()

        # Main widgets:
        self.__wstack  = QStackedWidget(self)
        self.__navbar  = NavBar(self)

        # Stack elements:
        self.__viewer = Viewer(self, min_zoom = 0.20, max_zoom = 4.0)
        self.__config = Config(self.__viewer.canvas, self.__wstack)
        self.__optima = Optimizer(self.__viewer.canvas, self)

        # Stack viewport and config widgets:
        self.__wstack.addWidget(self.__viewer)
        self.__wstack.addWidget(self.__config)
        self.__wstack.addWidget(self.__optima)

        # Menu and connections:
        self.__menu__()
        self.__connect__()

        # Set __widget as the central widget:
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.__navbar)
        self.setCentralWidget(self.__wstack)

        # Display GUI:
        self.showMaximized()

    def __menu__(self):

        __menu = self.menuBar()
        __menu.setNativeMenuBar(False)
        __menu.setObjectName("Climact Menu")

        __file_menu = __menu.addMenu("File")
        __edit_menu = __menu.addMenu("Edit")
        __view_menu = __menu.addMenu("View")
        __help_menu = __menu.addMenu("Help")

        action_new = __file_menu.addAction("New Project", QKeySequence("Ctrl+N"))

        __file_menu.addSeparator()
        action_import = __file_menu.addAction("Import Schema", QKeySequence.StandardKey.Open)
        action_export = __file_menu.addAction("Export Schema", QKeySequence.StandardKey.Save)

        __file_menu.addSeparator()
        action_quit   = __file_menu.addAction("Quit", QKeySequence.StandardKey.Quit)

        __edit_menu.addSeparator()
        action_settings = __edit_menu.addAction("Settings", QKeySequence("Ctrl+,"))

        action_zoom_in  = __view_menu.addAction("Zoom In" , QKeySequence("Ctrl+="))
        action_zoom_out = __view_menu.addAction("Zoom Out", QKeySequence("Ctrl+-"))
        action_reset    = __view_menu.addAction("Reset FOV", QKeySequence("Ctrl+0"))
        __view_menu.addSeparator()

        action_toolbar    = __view_menu.addAction("Toggle Toolbar", QKeySequence("Ctrl+T"))
        action_fullscreen = __view_menu.addAction("Toggle Fullscreen", QKeySequence("Ctrl+F"))

        action_help      = __help_menu.addAction("About", QKeySequence("Ctrl+I"))
        action_shortcuts = __help_menu.addAction("Shortcuts", QKeySequence("Ctrl+."))

        action_zoom_in.triggered.connect(lambda: self.__viewer.zoom( 120))
        action_zoom_out.triggered.connect(lambda: self.__viewer.zoom(-120))

        action_toolbar.triggered.connect(lambda: self.__navbar.setVisible(not self.__navbar.isVisible()))
        action_reset.triggered.connect(self.__viewer.reset_scale)
        action_fullscreen.triggered.connect(self.showFullScreen)

        action_import.triggered.connect(self.__viewer.canvas.import_json)
        action_export.triggered.connect(self.__viewer.canvas.export_json)

    def __connect__(self):

        # Connect the nav-bar's actions to appropriate slots:
        self.__navbar.button_open.triggered.connect(self.__viewer.canvas.import_json)
        self.__navbar.button_save.triggered.connect(self.__viewer.canvas.export_json)

        self.__navbar.button_canvas.triggered.connect(lambda: self.__wstack.setCurrentWidget(self.__viewer))
        self.__navbar.button_sheets.triggered.connect(lambda: self.__wstack.setCurrentWidget(self.__config))
        self.__navbar.button_optima.triggered.connect(lambda: self.__wstack.setCurrentWidget(self.__optima))
        self.__navbar.button_assist.triggered.connect(lambda: self.__viewer.assistant.setVisible(self.__navbar.button_assist.isChecked()))
        self.__navbar.button_library.triggered.connect(lambda: self.__viewer.library.setVisible(self.__navbar.button_library.isChecked()))
        self.__viewer.library.sig_close.connect(self.__navbar.button_library.trigger)

        self.__config.sig_auto_open_config.connect(lambda: self.__wstack.setCurrentWidget(self.__config))


