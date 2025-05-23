import logging
from json import JSONDecodeError
from pathlib import Path

from PyQt6.QtCore import (
    Qt, 
    QtMsgType, 
    pyqtSignal,
    pyqtSlot
)

from PyQt6.QtWidgets import (
    QMenu,
    QTabBar,
    QWidget,
    QCheckBox,
    QTabWidget,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QApplication
)

from tabs.schema import *
from custom      import Message

class TabBar(QTabBar):

    # Signals:
    sig_rename_tab = pyqtSignal(int)
    sig_delete_tab = pyqtSignal(int)

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize super-class:
        super().__init__(parent)

        # Customize behavior:
        self.setTabsClosable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)

        # Context-menu:
        self._cpos = None
        self._menu = QMenu(self)

        # Menu-actions:
        _rename = self._menu.addAction("Rename")
        _delete = self._menu.addAction("Delete")

        # Connect action to signal:
        _rename.triggered.connect(lambda: self.sig_rename_tab.emit(self.tabAt(self.mapFromGlobal(self._cpos))))
        _delete.triggered.connect(lambda: self.sig_delete_tab.emit(self.tabAt(self.mapFromGlobal(self._cpos))))

    # Handles context-menu events:
    def contextMenuEvent(self, event):
        self._cpos = event.globalPos()
        self._menu.exec(self._cpos)

class Tabber(QTabWidget):

    # Global constants:
    _MAX_TAB = 8

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize super-class:
        super().__init__(parent)

        # Customize behaviour:
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabCloseRequested.connect(self.removeTab)

        # Customize behaviour:
        _tab_bar = TabBar(self)
        _tab_bar.sig_rename_tab.connect(self.rename_tab)
        _tab_bar.sig_delete_tab.connect(self.removeTab)

        self.setTabBar(_tab_bar)

        # Corner widget:
        self._cbox = QCheckBox("Save As")
        self._cbox.setChecked(True)

        # Create first tab:
        self.addTab()
        self.setCornerWidget(self._cbox)

    # Slot to create new tabs:
    @pyqtSlot()
    @pyqtSlot(Viewer)
    @pyqtSlot(Viewer, str)
    def addTab(self, _viewer: Viewer | None = None, _label: str | None = None):

        # Max tab-count:
        if self.count() >= 8:
            print(f"Max tab-count reached!")
            QApplication.beep()
            return

        # Null-check:
        if not bool(_viewer):   _viewer = Viewer(self)
        if not bool(_label):    _label  = f"Untitled_{self.count() + 1}*"

        # Only accept widgets of type `Viewer`:
        if not isinstance(_viewer, Viewer): return

        # Connect viewer's signals:
        _viewer.canvas.sig_canvas_state.connect(self.set_indicator)
        _viewer.canvas.sig_schema_setup.connect(lambda file: self.setTabText(
            self.currentIndex(),
            Path(file).name.split('.')[0]
        ))

        # Call super-class implementation:
        super().addTab(_viewer, _label)

    # Slot to remove tab:
    @pyqtSlot(int)
    def removeTab(self, _index):

        # Get currently active `Viewer`:
        _viewer = self.widget(_index)
        _viewer.close()

        if _viewer.closed:
            super().removeTab(_index)   # Call super-class implementation:

    @pyqtSlot(int)
    def rename_tab(self, _index):
        name, code = QInputDialog.getText(self, "Rename Tab", "Enter new name:")
        if code: self.setTabText(_index, f"{name}*")

    # Toggle assistant:
    def toggle_assistant(self): self.currentWidget().toggle_assistant()

    # Import schematic:
    def import_schema(self):

        _index  = self.currentIndex ()  # Get index of the current widget
        _viewer = self.currentWidget()  # Get current widget

        # Type-check:
        if (
            isinstance(_viewer, Viewer) and
            isinstance(_viewer.canvas, Canvas)
        ):
            _file = _viewer.canvas.import_schema()      # Forward action to the canvas, get name of the opened file
            if  _file:
                _stem = Path(_file).stem                    # Extract stem from filename
                self.setTabText(_index, _stem)  # Rename the current tab to the stem

    # Export schematic:
    def export_schema(self):

        _viewer = self.currentWidget()  # Get current widget
        _index  = self.currentIndex ()  # Get current index
        _stem   = self.tabText(_index)  # Get tab-label
        _stem   = _stem.replace("*", "")    # Remove asterisk from label

        # Type-check:
        if (
            not isinstance(_viewer, Viewer) or
            not isinstance(_viewer.canvas, Canvas)
        ):
            Message.warning(None,
                           "Climact: Warning",
                           "Invalid viewer or canvas, cannot save file!"
                            )
            return None

        _name = f"{_stem}.json" if self._cbox.isChecked() \
                                else QFileDialog.getSaveFileName(None,
                                                                "Enter filename", ".",
                                                                "JSON (*.json)"
                                                                )[0]

        # Export schematic as JSON:
        try:
            _canvas = _viewer.canvas   # Get canvas
            _canvas.export_schema(f"{_name}")       # Save schematic
            self.set_indicator(SaveState.SAVED)     # Remove asterisk from tab label

        except (RuntimeError, JSONDecodeError) as error:

            Message.critical(None, "Climact: Error", "An error occurred. Please check logfile for details!")
            logging.critical(error)

    # Set/Unset the modified indicator:
    @pyqtSlot(SaveState)
    def set_indicator(self, _state: SaveState):

        # Validate argument(s):
        if not isinstance(_state, SaveState): raise TypeError("Expected argument of type `SaveState`")

        # Get current index and label:
        _index = self.indexOf(self.currentWidget())
        _label = self.tabText(_index)

        # Display `UNSAVED` indicator (asterisk):
        if  _state == SaveState.UNSAVED and not _label.endswith('*'):
            self.setTabText(_index, f"{_label}*")

        # Remove `UNSAVED` indicator (asterisk):
        elif _state == SaveState.SAVED and _label.endswith('*'):
            self.setTabText(_index, f"{_label.split('*')[0]}")