from linecache import clearcache

from PyQt6.QtCore import (
    Qt,
    pyqtSignal
)

from PyQt6.QtWidgets import (
    QLabel,
    QDialog,
    QWidget,
    QLineEdit,
    QVBoxLayout, QDialogButtonBox,
)

class Getter(QDialog):
    """
    A dialog that prompts the user for input with a label and a QLineEdit widget.
    """

    # Initializer:
    def __init__(
        self,
        label: str,
        hints: str,
        parent: QWidget | None = None,
        flags: Qt.WindowType = Qt.WindowType.Window
    ):
        # Initialize super-class:
        super().__init__(parent, flags)

        # Set attributes:
        self.setStyleSheet(
            "QDialog, QDialog QLineEdit {"
            "margin: 0px;"
            "padding: 0px;"
            "color: white;"
            "background-color: lightslategray;"
            "}"
        )

        # Create widgets:
        self._label = QLabel(label, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._entry = QLineEdit(self)
        self._entry.setPlaceholderText(hints)
        self._entry.returnPressed.connect(self.accept)

        # Create a layout and add the QLineEdit widget:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(16)

        layout.addWidget(self._label)
        layout.addWidget(self._entry)

        # Set the layout for the dialog:
        self.setLayout(layout)

    # Getter method to retrieve the text from the QLineEdit widget:
    def text(self) -> str:
        """
        Returns the text entered in the QLineEdit widget.

        :return: The text entered in the QLineEdit widget, stripped of leading and trailing whitespace.
        """
        return self._entry.text().strip()