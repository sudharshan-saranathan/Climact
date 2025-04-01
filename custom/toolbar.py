from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QAction, QIcon
from PyQt6.QtWidgets import QToolBar

class ToolBar(QToolBar):

    # Signals:
    sig_folder_clicked = pyqtSignal(name="Open")
    sig_floppy_clicked = pyqtSignal(name="Save")
    sig_sheets_clicked = pyqtSignal(name="Sheets")
    sig_python_clicked = pyqtSignal(name="Optima")

    def __init__(self, parent=None):

        # Initialize base-class:
        super().__init__(parent)

        # Load icons from file:
        self._sheets_icon = QPixmap("rss/icons/sheets.png")
        self._folder_icon = QPixmap("rss/icons/folder.png")
        self._floppy_icon = QPixmap("rss/icons/floppy.png")
        self._python_icon = QPixmap("rss/icons/python.png")

        self._action_load   = QAction(QIcon(self._folder_icon), "Load Schematic", self)
        self._action_save   = QAction(QIcon(self._floppy_icon), "Save Schematic", self)
        self._action_sheets = QAction(QIcon(self._sheets_icon), "Database", self)
        self._action_python = QAction(QIcon(self._python_icon), "Optimize", self)

        self.setIconSize(QSize(32, 24))
        self.addAction(self._action_load)
        self.addAction(self._action_save)
        self.addAction(self._action_sheets)
        self.addAction(self._action_python)

        # Connect actions to slots:
        self._action_load.triggered.connect(self.sig_folder_clicked.emit)
        self._action_save.triggered.connect(self.sig_floppy_clicked.emit)
        self._action_sheets.triggered.connect(self.sig_sheets_clicked.emit)
        self._action_python.triggered.connect(self.sig_python_clicked.emit)
