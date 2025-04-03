from PyQt6.QtWidgets import QWidget, QLabel


class SettingsAMPL(QWidget):

    def __init__(self, parent: QWidget | None):

        super().__init__(parent)

        # Main widgets:

        # Labels:
        __solver       = QLabel("Solver", self)
        __presolve_eps = QLabel("Presolve tolerance")
