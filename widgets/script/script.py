from PyQt6.QtWidgets import QTextEdit, QWidget

class Script(QTextEdit):

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)