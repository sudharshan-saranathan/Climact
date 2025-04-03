from dataclasses import dataclass

from PyQt6.QtCore    import Qt, QRectF, pyqtSlot
from PyQt6.QtGui     import *
from PyQt6.QtWidgets import *

from widgets            import schema, gemini
from library import ComponentLibrary

class Viewer(QGraphicsView):

    # Zoom-attrib:
    @dataclass()
    class Zoom:
        exp = 1.1
        val = 1.0
        max = 4.0
        min = 0.2

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # Assign keyword keys:
        max_zoom = kwargs.get("max_zoom")
        min_zoom = kwargs.get("min_zoom")
        x_bounds = kwargs.get("x_bounds") if isinstance(kwargs.get("x_bounds"), float) else 25000.0
        y_bounds = kwargs.get("y_bounds") if isinstance(kwargs.get("y_bounds"), float) else 25000.0

        # Viewport behaviour:
        self.setRenderHint(QPainter.RenderHint.Antialiasing)                                # Prevents pixelation (do not remove)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)                             # Enables click-and-drag panning
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)     # Prevents artifacts (do not remove)

        # Default zoom-attribute(s):
        self.__zoom = self.Zoom()
        self.__zoom.min = min_zoom
        self.__zoom.max = max_zoom

        # Initialize Canvas (QGraphicsScene derivative)
        self.__canvas = schema.Canvas(QRectF(0, 0, x_bounds, y_bounds), self)
        self.setScene(self.__canvas)

        # Layout to manage additional widgets:
        __layout = QGridLayout(self)
        __layout.setContentsMargins(4, 4, 16, 16)
        __layout.setSpacing(0)

        # Library:
        self.__library = ComponentLibrary(None)
        self.__library.setFixedWidth(400)

        self.__library.library['Components'].sig_template_selected.connect(self.import_template)
        # self.__library.library['Systems']   .sig_template_selected.connect(self.import_template)

        # Gemini AI assistant:
        self.__gemini = gemini.Gui(self.canvas, None)
        self.__gemini.hide()

        # Layout overlaid on central graph:
        __layout.addWidget(self.__library, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft   | Qt.AlignmentFlag.AlignBottom)
        __layout.addWidget(self.__gemini , 0, 1, 1, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        __layout.setColumnStretch(0, 10)
        __layout.setColumnStretch(2, 10)

        # Define shortcuts:
        shortcut_ctrl_a = QShortcut(QKeySequence.StandardKey.SelectAll, self)
        shortcut_ctrl_v = QShortcut(QKeySequence.StandardKey.Paste, self)
        shortcut_delete = QShortcut(QKeySequence.StandardKey.Delete, self)

        shortcut_ctrl_a.activated.connect(self.canvas.select)
        shortcut_ctrl_v.activated.connect(self.canvas.copy)
        shortcut_delete.activated.connect(self.canvas.delete)

    @property
    # GUI of the AI assistant:
    def assistant(self):
        return self.__gemini

    @property
    # Canvas:
    def canvas(self):
        return self.__canvas

    @property
    # Library:
    def library(self):
        return self.__library

    # Event-handler for key-press events:
    def keyPressEvent(self, event):

        # Pass to super, return if event is handled (by other items):
        super().keyPressEvent(event)
        if event.isAccepted():
            return

        # When Alt is pressed, switch to rubberband drag mode:
        if event.modifiers() == Qt.KeyboardModifier.AltModifier:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return

    # Event-handler for key-press events:
    def keyReleaseEvent(self, event):

        super().keyReleaseEvent(event)
        if event.isAccepted():
            return

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # Event-handler for scrolling events:
    def wheelEvent(self, event):

        # Get angle-change and call zoom():
        adelta = event.angleDelta().y()
        self.zoom(adelta)

    # Zoom implementation:
    def zoom(self, delta: float):

        scroll = delta / 100
        factor = pow(self.__zoom.exp, scroll)

        # Clip scaling factor if the zoom is near max/min:
        if scroll > 0 and self.__zoom.val * factor >= self.__zoom.max:
            factor = self.__zoom.max / self.__zoom.val

        elif scroll < 0 and self.__zoom.val * factor <= self.__zoom.min:
            factor = self.__zoom.min / self.__zoom.val

        # Rescale the field of view:
        self.__zoom.val *= factor
        self.scale(factor, factor)

    def reset_scale(self):
        factor = 1.0 / self.__zoom.val
        self.scale(factor, factor)
        self.__zoom.val = 1.0

    @pyqtSlot(QToolButton)
    def import_template(self, button: QToolButton):

        folder = button.objectName()
        __file = f"library/{folder.lower()}/{button.text()}.json"

        with open(__file, "r") as file:
            code = file.read()
            print(f"INFO: Loading template from {file}")
            print(f"{code}")
            schema.JsonLib.decode_json(code, self.canvas)
