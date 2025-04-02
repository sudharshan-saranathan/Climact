from PyQt6.QtCore    import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QWidget, QGridLayout, QCheckBox, QButtonGroup


class Input(QDialog):

    # Initializer:
    def __init__(self, parent: QWidget | None, **kwargs):

        # Initialize base-class:
        super().__init__(None)

        # Assign keyword keys:
        message = kwargs.get("prompt")
        radio_b = kwargs.get("option")

        first  = kwargs.get("option_first")
        second = kwargs.get("option_second")

        # Customize flags:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("QDialog {border-radius: 4px;}")
        self.setContentsMargins(0, 0, 0, 0)

        # Main widgets:
        self.__input = QLineEdit()
        self.__input.returnPressed.connect(self.accept)

        self.__label = QLabel(message)
        self.__label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__label.setStyleSheet("QLabel {border: none; background: #81909C; color: white;}")
        self.__input.setStyleSheet("QLineEdit {background: #81909C; color: white; margin: 0px;}")
        self.__input.setTextMargins(0, 0, 0, 0)

        # Checkboxes and button-group:
        self.__sys_check = QCheckBox(first)
        self.__com_check = QCheckBox(second)
        self.__com_check.setChecked(True)

        __button_group = QButtonGroup(self)
        __button_group.addButton(self.__com_check)
        __button_group.addButton(self.__sys_check)

        # Layout:
        __layout = QGridLayout(self)
        __layout.addWidget(self.__label, 0, 0, Qt.AlignmentFlag.AlignHCenter)
        __layout.addWidget(self.__input, 1, 0)

        if radio_b:
            __layout.addWidget(self.__com_check, 0, 1)
            __layout.addWidget(self.__sys_check, 1, 1)

        __layout.setContentsMargins(8, 8, 8, 8)
        __layout.setSpacing(4)

    @property
    def field(self):
        return self.__input.text()

    @property
    def option(self):
        return self.__com_check.text() if self.__com_check.isChecked() else self.__sys_check.text()
