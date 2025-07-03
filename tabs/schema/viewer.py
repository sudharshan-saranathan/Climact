#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------
import types
import logging
import dataclasses
from json import JSONDecodeError

from PyQt6.QtGui import (
    QPainter,
    QShortcut,
    QKeySequence
)

from PyQt6.QtCore import (
    Qt,
    QRectF,
    QTimer,
    QEvent,
    pyqtSlot,
    pyqtSignal,
    pyqtProperty,
    QEasingCurve,
    QPropertyAnimation
)

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGraphicsView
)

from config import ViewerConfig
from custom.entity  import EntityClass
from custom.dialog import Dialog
from dataclasses   import dataclass
from tabs.gemini   import widget
from util          import *

from .jsonio import JsonIO
from .canvas  import Canvas, CanvasState

# Class: Viewer
class Viewer(QGraphicsView):

    # Signals:
    sig_json_loaded = pyqtSignal(str)

    # Initializer:
    def __init__(self, _parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(_parent)
        super().setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        # Assign keyword keys:
        x_bounds = kwargs.get("x_bounds", 10000)
        y_bounds = kwargs.get("y_bounds", 10000)

        # Default zoom-attribute(s):
        self._zoom = types.SimpleNamespace(
            exp = 1.4,                          # Zoom factor
            val = 1.0,                          # Current zoom value
            max = kwargs.get("max_zoom", 5.0),  # Maximum zoom value
            min = kwargs.get("min_zoom", 0.2)   # Minimum zoom value
        )

        # Zoom-animation:
        self._zoom_val  = self._zoom.val
        self._zoom_anim = QPropertyAnimation(self, b"animated_zoom")
        self._zoom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._zoom_anim.setDuration(200)  # Animation duration in milliseconds

        # Initialize Canvas (QGraphicsScene derivative)
        self.canvas = Canvas(
            QRectF(0, 0, x_bounds, y_bounds),
            self
        )

        self.canvas.sig_schema_setup.connect(self.sig_json_loaded)
        self.setScene(self.canvas)

        # Gemini AI assistant:
        self._gemini = widget.Gui(self.canvas)
        self._gemini.hide()

        # Layout to manage widgets:
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(4, 4, 16, 16)
        layout.addWidget(self._gemini, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.insertStretch(0, 10)

        # Action shortcuts:
        QShortcut(QKeySequence("Ctrl+N"), self, self.canvas.create_node)
        QShortcut(QKeySequence("Ctrl+["), self, lambda: self.canvas.create_terminal(EntityClass.OUT))
        QShortcut(QKeySequence("Ctrl+]"), self, lambda: self.canvas.create_terminal(EntityClass.INP))
        QShortcut(QKeySequence.StandardKey.Paste, self, self.canvas.clone)
        QShortcut(QKeySequence.StandardKey.Copy , self, self.canvas.store)
        QShortcut(QKeySequence.StandardKey.Find , self, self.canvas.find_items)
        QShortcut(QKeySequence.StandardKey.Delete   , self, lambda: self.canvas.delete_items(set(self.canvas.selectedItems())))
        QShortcut(QKeySequence.StandardKey.SelectAll, self, lambda: self.canvas.select_items(self.canvas.node_db | self.canvas.term_db))

        shortcut_ctrl_z = QShortcut(QKeySequence.StandardKey.Undo, self, self.canvas.manager.undo)
        shortcut_ctrl_r = QShortcut(QKeySequence.StandardKey.Redo, self, self.canvas.manager.redo)
        shortcut_ctrl_z.activated.connect(lambda: self.canvas.sig_canvas_state.emit(CanvasState.HAS_UNSAVED_CHANGES))
        shortcut_ctrl_r.activated.connect(lambda: self.canvas.sig_canvas_state.emit(CanvasState.HAS_UNSAVED_CHANGES))

    # Handle user-driven zooming:
    def zoom(self, delta: int | float | None):
        factor = 1.0 / self._zoom.val if delta is None else self._zoom.exp ** (delta / 100.0)

        target_zoom = max(self._zoom.min, min(self._zoom.max, self._zoom.val * factor))
        ViewerConfig["zoom"] = target_zoom  # Save zoom level to config
        self._zoom_anim.stop()
        self._zoom_anim.setStartValue(self._zoom.val)
        self._zoom_anim.setEndValue(target_zoom)
        self._zoom_anim.start()

    @pyqtProperty(float)
    def animated_zoom(self):
        return self._zoom_val

    @animated_zoom.setter
    def animated_zoom(self, value):
        factor = value / self._zoom.val
        self.scale(factor, factor)
        self._zoom.val = value
        self._zoom_val = value

    # Toggles visibility of the AI assistant:
    def toggle_assistant(self):
        self._gemini.setEnabled(not self._gemini.isEnabled())
        self._gemini.setVisible(not self._gemini.isVisible())

    # Implement the JSON code into the canvas:
    def implement(self, code: str):

        try:
            JsonIO.decode(code, self.canvas, True)
            self.canvas.sig_canvas_state.emit(CanvasState.HAS_UNSAVED_CHANGES)

        except (RuntimeError, JSONDecodeError) as exception:
            Dialog.critical(None, "Error", f"Error decoding JSON: {exception}")
            return

    # Handle key-press events:
    def keyPressEvent(self, event):

        # Call super-class implementation, return if the event is accepted:
        super().keyPressEvent(event)
        if event.isAccepted():
            return

        # When Shift is pressed, switch to rubberband drag mode:
        if  event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

    # Handle key-release events:
    def keyReleaseEvent(self, event):
        # Call super-class implementation, return if the event is accepted:
        super().keyReleaseEvent(event)

        # Reset drag mode:
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # Handle scroll-events:
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom(float(delta))         # Zoom by the desired amount