import json
import logging

from pathlib import Path
from PyQt6.QtGui import QShortcut, QPainter, QKeySequence, QDrag
from PyQt6.QtCore import Qt, QRectF, pyqtSlot, QTimer, QMimeData, QByteArray
from PyQt6.QtWidgets    import QWidget, QGraphicsView, QGraphicsScene, QToolButton, QGridLayout, QMenu, QVBoxLayout

from dataclasses    import dataclass

from core.util import random_id
from tabs.gemini    import gemini, widget
from tabs.schema    import canvas
from tabs.schema.fileio import JsonLib

class Viewer(QGraphicsView):

    # Zoom-attrib:
    @dataclass()
    class Zoom:
        def __init__(self):
            self.exp = 1.1
            self.val = 1.0
            self.max = 4.0
            self.min = 0.2

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

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

        # Default zoom-attribute(s):
        self._zoom = self.Zoom()
        self._zoom.min = min_zoom if isinstance(min_zoom, float) else self._zoom.min
        self._zoom.max = max_zoom if isinstance(max_zoom, float) else self._zoom.max

        # Initialize Canvas (QGraphicsScene derivative)
        self.canvas = canvas.Canvas(QRectF(0, 0, x_bounds, y_bounds), self)
        self.setScene(self.canvas)

        # Layout to manage additional widgets:
        _layout = QVBoxLayout(self)
        _layout.setContentsMargins(4, 4, 16, 16)
        _layout.setSpacing(0)

        # Gemini AI assistant:
        self._gemini = widget.Gui(self)
        self._gemini.setEnabled(False)
        self._gemini.hide()
        self._gemini.sig_json_available.connect(self.process_json)

        # Layout overlaid on central graph:
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
        shortcut_ctrl_c.activated.connect(self.canvas.copy)
        shortcut_ctrl_v.activated.connect(self.canvas.paste)
        shortcut_ctrl_z.activated.connect(self.canvas.manager.undo)
        shortcut_ctrl_r.activated.connect(self.canvas.manager.redo)
        shortcut_ctrl_a.activated.connect(lambda: self.canvas.select_items(self.canvas.node_items | self.canvas.flow_items))
        shortcut_delete.activated.connect(lambda: self.canvas.delete_items(set(self.canvas.selectedItems())))

    def zoom(self, delta: int | float | None):
        factor = 1.0 / self._zoom.val if delta is None else self._zoom.exp ** (delta / 100.0)
        self._zoom.val *= factor
        self.scale(factor, factor)

    def toggle_assistant(self):
        self._gemini.setEnabled(not self._gemini.isEnabled())
        self._gemini.setVisible(not self._gemini.isVisible())

    def keyPressEvent(self, event):

        # Pass to super, return if event is handled (by other items):
        super().keyPressEvent(event)
        if event.isAccepted():
            return

        # When Shift is pressed, switch to rubberband drag mode:
        if  event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return

    def keyReleaseEvent(self, event):

        super().keyReleaseEvent(event)
        if event.isAccepted():
            return

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    def wheelEvent(self, event):
        # Get scroll magnitude and rescale:
        delta = event.angleDelta().y()
        self.zoom(float(delta))

    def process_json(self, json_code: str):

        # Null-check:
        if json_code is None: return

        # Decode:
        try: JsonLib.decode_json(json_code, self.canvas, True)
        except Exception as exception:
            print(f"An exception occurred when processing JSON")
            logging.exception(f"An exception occurred: {exception}")