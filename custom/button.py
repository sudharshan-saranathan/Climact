from PyQt6.QtCore import pyqtSignal
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtWidgets import QGraphicsItem

class Button(QGraphicsSvgItem):
    """
    A custom `QGraphicsSvgItem` that represents a button in a graphical scene.
    """
    # Default values:
    _svg_width = 256
    _svg_scale = 0.05

    # Signals:
    sig_button_clicked = pyqtSignal()

    # Class constructor:
    def __init__(self,
                 filepath,
                 parent: QGraphicsItem | None = None,
                 functor: callable = None):

        # Base-class initialization:
        super().__init__(filepath, parent)
        super().setScale(self._svg_scale)

        # Resize SVG-icon:
        center = self.boundingRect().center()

        # Accept hover events and re-position the button:
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(center)
        self.moveBy(-center.x(), -center.y())

        # If a callable is provided, connect it to the button click signal:
        self.sig_button_clicked.connect(functor) if functor else None

    def hoverEnterEvent(self, event):
        """
        Handle hover enter event to change the opacity of the button.
        :param event:
        """
        super().hoverEnterEvent(event)
        self.setOpacity(0.4)

    def hoverLeaveEvent(self, event):
        """
        Handle hover leave event to reset the opacity of the button.
        :param event:
        """
        super().hoverLeaveEvent(event)
        self.setOpacity(1.0)

    def mousePressEvent(self, event):
        """
        Handle mouse press event to emit a signal when the button is clicked.
        :param event:
        """
        self.setScale(0.055)
        self.sig_button_clicked.emit()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event to reset the scale of the button.
        :param event:
        """
        self.setScale(self._svg_scale)