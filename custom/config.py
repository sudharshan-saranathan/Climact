import qtawesome as qta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget, QGridLayout, QListWidget, QStackedWidget, QListWidgetItem, QPushButton, QFormLayout, QLabel, QLineEdit, QColorDialog

class StreamEditor(QWidget):

    def __init__(self, stream, parent: QWidget | None = None):
        super().__init__(parent)

        # Layout for the editor
        self._form = QGridLayout(self)
        self._form.setContentsMargins(2, 2, 2, 2)

        # Stream ID input
        self._strid = QLineEdit(stream.strid)
        self._color = QPushButton("Choose Color", self)

        # Add widgets to the layout:
        self._form.addWidget(QLabel("Stream ID:"), 0, 0)
        self._form.addWidget(self._strid, 0, 1, Qt.AlignmentFlag.AlignLeft)
        self._form.addWidget(QLabel("Color:"), 1, 0)
        self._form.addWidget(self._color, 1, 1, Qt.AlignmentFlag.AlignLeft)

# Class to configure resource-streams:
class StreamConfig(QDialog):

    # Constructor:
    def __init__(self, streams: set, parent: QWidget | None = None):
        super().__init__(parent)
        super().setFixedSize(300, 250)

        # Style:
        self.setStyleSheet("QListWidget {"
                           "border-radius: 8px;"
                           "}"
                           "QWidget {"
                           "border-radius: 8px;"
                           "}")

        # Define layout:
        self._list = QListWidget(self)
        self._edit = QStackedWidget(self)

        # Add streams:
        for stream in streams:
            self._list.addItem(stream.strid)
            self._edit.addWidget(StreamEditor(stream, self))

        self._grid = QGridLayout(self)
        self._grid.setSpacing(2)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.addWidget(self._list, 0, 0)
        self._grid.addWidget(self._edit, 0, 1)
        self._grid.setColumnStretch(1, 10)