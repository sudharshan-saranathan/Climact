from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget


class Separator(QFrame):

    # Initializer:
    def __init__(self, shape: QFrame.Shape, parent: QWidget | None, color: str = "#efefef"):

        # Initialize base-class:
        super().__init__(parent)

        # Style:
        self.setFrameShape(shape)
        self.setStyleSheet("QFrame {background: " + color + ";}")