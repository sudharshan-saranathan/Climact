from PyQt6.QtWidgets import QFrame, QButtonGroup, QWidget, QRadioButton, QHBoxLayout

# Class RadioButtonGroup(): Container for exclusive radio buttons
class RadioButtonGroup(QFrame):

    # Initializer:
    def __init__(self, labels: list[str], parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Main widgets:
        self.__buttons = list()
        self.__group   = QButtonGroup(None)     # Groups the radio buttons and makes them exclusive (default behaviour)

        # Create radio buttons with provided labels and add them to a QButtonGroup
        for label in labels:
            self.__button = QRadioButton(label)
            self.__button.setStyleSheet("QRadioButton {background: transparent;}")
            self.__buttons.append(self.__button)
            self.__group.addButton(self.__button)

        self.__buttons[0].setChecked(True)

        # Layout:
        __layout = QHBoxLayout(self)
        __layout.setContentsMargins(0, 0, 0, 0)
        __layout.setSpacing(8)

        for button in self.__buttons:
            __layout.addWidget(button)

        __layout.setStretch(2, 10)

    def selected(self):
        for button in self.__buttons:
            if button.isChecked():
                return button.text()

        return None