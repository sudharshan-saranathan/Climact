from PyQt6.QtCore import pyqtSignal
from PyQt6.QtSvgWidgets import QGraphicsSvgItem


class Button(QGraphicsSvgItem):

    # Default values:
    _svg_width = 256
    _svg_scale = 0.05

    # Signals:
    sig_button_clicked = pyqtSignal()

    def __init__(self, path, parent_item = None):

        # Base-class initialization:
        super().__init__(path, parent_item)

        # Resize SVG-icon:
        center = self.boundingRect().center()
        self.setTransformOriginPoint(center)
        self.setScale(self._svg_scale)

        # Accept hover events and re-position the button:
        self.setAcceptHoverEvents(True)
        self.moveBy(-center.x(), -center.y())

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setOpacity(0.4)

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.setOpacity(1.0)

    def mousePressEvent(self, event):
        self.setScale(0.055)
        self.sig_button_clicked.emit()

    def mouseReleaseEvent(self, event):
        self.setScale(self._svg_scale)