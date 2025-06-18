"""
viewer.py
---------
This module is part of the Climact application. It defines a custom class `Viewer` (subclass of `QGraphicsView`, see Qt
documentation for more details) for displaying and interacting with graphical content.
"""

__author__  = "Sudharshan Saranathan"
__version__ = "0.1.0"
__license__ = "None"
__date__    = "2025-05-26"

# Imports:
import util         # Climact module for utility functions
import types        # Standard library module for creating variables with dynamic attributes
import logging      # Standard library module for logging
import pydantic     # Standard library module for data validation and settings management

# PyQt6 modules:
from PyQt6.QtGui import QPainter, QShortcut, QKeySequence
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QGraphicsView,
    QGraphicsScene
)

# Climact module(s):
from .canvas import Canvas, CanvasState

# Class `Viewer`: A custom QGraphicsView for displaying and interacting with graphical content.
class Viewer(QGraphicsView):
    """
    A custom `QGraphicsView` for interacting with graphical content drawn on a `Canvas` (see `canvas.py`).
    """
    class ZoomAttr(pydantic.BaseModel):
        exp: float = pydantic.Field(1.05, description = "Exponent that controls zoom-speed")  # Exponent for zoom speed
        max: float = pydantic.Field(5.00, description = "Maximum zoom level")  # Maximum zoom level
        min: float = pydantic.Field(0.10, description = "Minimum zoom level")  # Minimum zoom level
        val: float = pydantic.Field(1.00, description = "Current zoom level")  # Current zoom level

        class Config:
            """
            Configuration for the ZoomAttr model.
            """
            validate_assignment = True  # Validate assignments to fields

    # Initializer:
    def __init__(self,
                 parent: QWidget | None,
                 **kwargs):

        # Initialize the QGraphicsView with the parent widget
        super().__init__(parent)

        # Define attribute(s):
        self._zoom = self.ZoomAttr(exp = kwargs.get('exp', 1.05),
                                   max = kwargs.get('max', 5.00),
                                   min = kwargs.get('min', 0.10),
                                   val = kwargs.get('val', 1.00))

        self._rect = types.SimpleNamespace(
            xs = util.as_float(kwargs.get('xs', 25000.0)),
            ys = util.as_float(kwargs.get('ys', 25000.0))
        )

        # Set the scene for this viewport and adjust other properties:
        self.setObjectName(util.random_id(prefix='V'))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)

        # Instantiate a QGraphicsScene and set it as the scene for this view:
        self.canvas = Canvas(self._rect.xs, self._rect.ys, self)
        self.setScene(self.canvas)

        # Initialize shortcuts:
        QShortcut(QKeySequence.StandardKey.Copy , self, self.canvas.clone_items)
        QShortcut(QKeySequence.StandardKey.Paste, self, self.canvas.paste_items)
        QShortcut(QKeySequence.StandardKey.Undo , self, self.canvas.manager.undo)
        QShortcut(QKeySequence.StandardKey.Redo , self, self.canvas.manager.redo)
        QShortcut(QKeySequence.StandardKey.Find , self, self.canvas.find_items)
        QShortcut(QKeySequence.StandardKey.Delete, self, lambda: self.canvas.delete_items(self.canvas.selectedItems()))
        QShortcut(QKeySequence.StandardKey.SelectAll, self, self.canvas.select_all)

    # Wheel event for zooming in and out:
    def wheelEvent(self, event) -> None:
        """
        Event handler for mouse wheel events to zoom in and out of the scene.

        :param event:
        """
        delta = event.angleDelta().y()
        self.rescale_fov(float(delta))

    # Event-handler for keyboard events:
    def keyPressEvent(self, event):
        """
        Handles key press events to switch to rubberband drag mode when Shift is pressed.
        :param event:
        """
        # Call super-class implementation, return if event is accepted:
        super().keyPressEvent(event)
        if  event.isAccepted():
            return

        # When Shift is pressed, switch to rubberband drag mode:
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()

    # Handle key-release events:
    def keyReleaseEvent(self, event):
        """
        Handles key release events to reset the cursor and drag mode when Shift is released.
        :param event:
        """
        # Call super-class implementation, return if event is accepted:
        super().keyReleaseEvent(event)

        # Reset cursor and drag-mode:
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # Zoom logic:
    def rescale_fov(self, delta: int | float | None) -> None:
        """
        Zooms in or out of the scene based on the mouse wheel movement.

        :param delta: The amount to zoom in or out.
        """

        if delta is None:   factor = 1.0 / self._zoom.val                 # If delta is None, reset zoom.
        else            :   factor = self._zoom.exp ** (delta / 100.0)    # Otherwise, calculate zoom factor.

        self._zoom.val *= factor # Update the zoom value
        self.scale(factor, factor) # Rescale the viewport

    # Imports a new project into the viewer:
    def import_project(self, project: str, clear: bool = False) -> None:
        """
        Imports a new project into the viewer.

        :param: project (str): The path to the project file to be imported.
        """

        # If the `clear` flag is set, clear the canvas:
        if clear: self.canvas.clear()

        # Update the viewport:
        self.viewport().update()

    # Exports the currently visible schematic as a JSON file:
    def export_project(self, project: str) -> None:
        """
        Exports the currently visible schematic as a JSON file.

        :param: project (str): The path where the project file will be saved.
        """

        # For now, this method does nothing:
        pass