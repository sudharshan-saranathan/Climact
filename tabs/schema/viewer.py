#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------

import logging
from json import JSONDecodeError

from PyQt6.QtGui import (
    QPainter,
    QShortcut,
    QKeySequence
)

from PyQt6.QtCore import (
    Qt, 
    QRectF, 
    pyqtSlot, 
    pyqtSignal, 
    QtMsgType, 
    QEvent
)

from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QGraphicsView, 
    QVBoxLayout,
    QMessageBox
)

from custom.message import Message
from dataclasses   import dataclass
from tabs.gemini   import widget
from util          import *

from .jsonlib import JsonLib
from .canvas  import Canvas, SaveState

# Class: Viewer
class Viewer(QGraphicsView):
    """
    """

    # Signals:
    sig_has_changed = pyqtSignal(bool)
    sig_json_loaded = pyqtSignal(str)

    # Zoom-attrib:
    @dataclass()
    class Zoom:
        def __init__(self):
            self.exp = 1.1
            self.val = 1.0
            self.max = 4.0
            self.min = 0.2

    # Initializer:
    def __init__(self, _parent: QWidget | None, **kwargs):
        """
        Initializes the Viewer class.

        Args:
            parent (QWidget | None): The parent widget.
            **kwargs: Keyword arguments.
        """

        # Initialize base-class:
        super().__init__(_parent)

        # Assign keyword keys:
        max_zoom = kwargs.get("max_zoom") if "max_zoom" in kwargs else 4.0
        min_zoom = kwargs.get("min_zoom") if "min_zoom" in kwargs else 0.2
        x_bounds = kwargs.get("x_bounds") if isinstance(kwargs.get("x_bounds"), float) else 25000.0
        y_bounds = kwargs.get("y_bounds") if isinstance(kwargs.get("y_bounds"), float) else 25000.0

        # Viewport behaviour:
        self.setObjectName(random_id(length=4, prefix='V'))                                 # Schematic Viewer UID
        self.setRenderHint(QPainter.RenderHint.Antialiasing)                                # Prevents pixelation (do not remove)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)                             # Enables click-and-drag panning
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)     # Prevents artifacts (do not remove)
        logging.info("Anti-aliasing enabled.")
        logging.info("Click-and-drag enabled.")
        logging.info("Full-viewport update enabled.")

        # Default zoom-attribute(s):
        self._zoom = self.Zoom()
        self._zoom.min = min_zoom if isinstance(min_zoom, float) else self._zoom.min
        self._zoom.max = max_zoom if isinstance(max_zoom, float) else self._zoom.max

        # Initialize Canvas (QGraphicsScene derivative)
        self.closed = False
        self.state  = SaveState.UNSAVED
        self.canvas = Canvas(QRectF(0, 0, x_bounds, y_bounds), self)
        self.setScene(self.canvas)

        self.canvas.sig_canvas_state.connect(self.update_state)
        self.canvas.sig_schema_setup.connect(self.sig_json_loaded)
        logging.info(f"Canvas [UID = {self.canvas.uid}] initialized.")

        # Gemini AI assistant:
        self._gemini = widget.Gui(self.canvas)
        self._gemini.setEnabled(False)
        self._gemini.hide()
        self._gemini.sig_json_available.connect(self.execute_json)
        logging.info(f"Gemini AI-assistant initialized.")

        # Layout to manage widgets:
        _layout = QVBoxLayout(self)
        _layout.setSpacing(0)
        _layout.setContentsMargins(4, 4, 16, 16)
        _layout.addWidget(self._gemini, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        _layout.insertStretch(0, 10)

        # Define shortcuts:
        shortcut_ctrl_a = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        shortcut_ctrl_v = QShortcut(QKeySequence.StandardKey.Paste, self)
        shortcut_ctrl_c = QShortcut(QKeySequence.StandardKey.Copy, self)
        shortcut_ctrl_z = QShortcut(QKeySequence.StandardKey.Undo, self)
        shortcut_ctrl_r = QShortcut(QKeySequence.StandardKey.Redo, self)
        shortcut_delete = QShortcut(QKeySequence.StandardKey.Delete, self)

        # Activate shortcuts:
        shortcut_ctrl_z.activated.connect(self.canvas.manager.undo)
        shortcut_ctrl_r.activated.connect(self.canvas.manager.redo)
        shortcut_ctrl_c.activated.connect(self.canvas.store)
        shortcut_ctrl_v.activated.connect(self.canvas.clone)
        shortcut_ctrl_z.activated.connect(lambda: self.canvas.sig_canvas_state.emit(SaveState.UNSAVED))
        shortcut_ctrl_r.activated.connect(lambda: self.canvas.sig_canvas_state.emit(SaveState.UNSAVED))
        shortcut_ctrl_a.activated.connect(lambda: self.canvas.select_items(self.canvas.node_db | self.canvas.term_db))
        shortcut_delete.activated.connect(lambda: self.canvas.delete_items(set(self.canvas.selectedItems())))

        logging.info(f"Viewer [UID = {self.objectName()}] initialized.")

    @property
    def uid(self)   -> str:  return self.objectName()

    @uid.setter
    def uid(self, value: str):   self.setObjectName(value if isinstance(value, str) else self.uid)

    # Handle user-driven zooming:
    def zoom(self, delta: int | float | None):
        factor = 1.0 / self._zoom.val if delta is None else self._zoom.exp ** (delta / 100.0)
        self._zoom.val *= factor
        self.scale(factor, factor)

    # Toggles visibility of AI-assistant:
    def toggle_assistant(self):
        self._gemini.setEnabled(not self._gemini.isEnabled())
        self._gemini.setVisible(not self._gemini.isVisible())

    def execute_json(self, json_data: str):

        if  json_data:

            try: JsonLib.decode(json_data, self.canvas, True)
            except (RuntimeError, JSONDecodeError) as exception:
                Message.critical(None, "Error", f"Error decoding JSON: {exception}")
                logging.critical(exception)
                return

            self.state = SaveState.UNSAVED
            self.canvas.sig_canvas_state.emit(SaveState.UNSAVED)

    # Register the canvas' saved/unsaved state:
    def update_state(self, state: SaveState):   self.state = state

    # Handle key-press events:
    def keyPressEvent(self, event):

        # Call super-class implementation, return if event is accepted:
        super().keyPressEvent(event)
        if event.isAccepted():
            return

        # When Shift is pressed, switch to rubberband drag mode:
        if  event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()

    # Handle key-release events:
    def keyReleaseEvent(self, event):

        # Call super-class implementation, return if event is accepted:
        super().keyReleaseEvent(event)
        if event.isAccepted():
            return

        # Reset cursor and drag-mode:
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # Handle scroll-events:
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom(float(delta))         # Zoom by desired amount

    # Handle close-events:
    @pyqtSlot(QEvent)
    def closeEvent(self, event):

        # Print save-state:
        print(str(self.canvas.state))

        # Check if canvas has been modified:
        if self.canvas.state == SaveState.UNSAVED:

            # Confirm quit:
            _dialog = Message(QtMsgType.QtWarningMsg,
                         "Do you want to save unsaved changes?",
                              QMessageBox.StandardButton.Yes |
                              QMessageBox.StandardButton.No |
                              QMessageBox.StandardButton.Cancel
                              )

            # Execute dialog and get result:
            _dialog_code = _dialog.exec()

            # Handle close-event accordingly:
            if _dialog_code == QMessageBox.StandardButton.Yes:
                self.closed = True
                event.accept()

            if _dialog_code == QMessageBox.StandardButton.No:
                self.closed = True
                event.accept()

            if _dialog_code == QMessageBox.StandardButton.Cancel:
                self.closed = False
                event.ignore()

        # Close directly
        else:
            self.closed = True
            event.accept()