import logging

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
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QApplication
)

from tabs.schema.viewer import Viewer
from tabs.schema.canvas import SaveState
from custom import Dialog

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
        _viewer.canvas.sig_schema_setup.connect(lambda file: 
                                                    self.setTabText(
                                                        self.currentIndex(), 
                                                        file
                                                    )
                                                )

        # Call super-class implementation:
        super().addTab(_viewer, _label)

    # Slot to remove tab:
    @pyqtSlot(int)
    def removeTab(self, _index):

        # Delete widget:
        widget = self.widget(_index)
        widget.close()

        # Call super-class implementation:
        super().removeTab(_index)

    @pyqtSlot(int)
    def rename_tab(self, _index):
        name, code = QInputDialog.getText(self, "Rename Tab", "Enter new name:")
        if code: self.setTabText(_index, f"{name}*")

    # Toggle assistant:
    def toggle_assistant(self): self.currentWidget().toggle_assistant()

    # Import schematic:
    def import_schema(self):    self.currentWidget().canvas.import_schema()

    # Export schematic:
    def export_schema(self):

        # Trigger save:
        if  self._cbox.isChecked():
            _save_name = self.tabText(self.currentIndex())  # Save file-name is the same as tab label
            _save_name = _save_name.split('*')[0]           # Remove `*` from save-name

            try:
                _canvas = self.currentWidget().canvas       # Get canvas
                _canvas.export_schema(f"{_save_name}.json") # Save schematic
                self.set_indicator(SaveState.SAVED)         # Modify indicator

            except Exception as exception:
                logging.exception(f"An exception occurred: {exception}")

        else:
            # File-dialog:
            _file, _code = QFileDialog.getSaveFileName(None, "Select JSON file", "./", "JSON files (*.json)")\

            if _code:
                try:
                    _canvas = self.currentWidget().canvas   # Get canvas
                    _canvas.export_schema(f"{_file}")       # Save schematic
                    self.set_modified(False)                # Remove asterisk from tab label

                except Exception as exception:
                    
                    # Instantiate error-dialog:
                    _error_dialog = Dialog(QtMsgType.QtCriticalMsg,
                                f"An exception occurred: {exception}",
                                   QMessageBox.StandardButton.Ok)
                    logging.exception(f"An exception occurred: {exception}")

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