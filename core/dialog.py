from PyQt6.QtCore       import QtMsgType
from PyQt6.QtWidgets    import QMessageBox, QWidget
from dataclasses        import dataclass

# Class Dialog:
class Dialog(QMessageBox):

    # Default attribute(s):
    @dataclass
    class Attr:
        title = "Dialog"
        width =  500

    # Initializer:
    def __init__(self,
                 msg_type       : QtMsgType,
                 msg_string     : str,
                 default_button : QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
                 default_parent : QWidget = None):

        # Initialize base-class:
        super().__init__(default_parent)

        # Customize appearance and message:
        self.setWindowTitle(self.Attr.title)
        self.setFixedWidth (self.Attr.width)

        # Display message:
        self.setText(msg_string)
        if msg_type == QtMsgType.QtInfoMsg:
            self.setIcon(QMessageBox.Icon.Information)

        elif msg_type == QtMsgType.QtWarningMsg:
            self.setIcon(QMessageBox.Icon.Warning)

        elif msg_type == QtMsgType.QtCriticalMsg:
            self.setIcon(QMessageBox.Icon.Critical)

        elif msg_type == QtMsgType.QtFatalMsg:
            self.setIcon(QMessageBox.Icon.Critical)

        # Default buttons:
        self.setStandardButtons(default_button)

        # Customize the cancel-button:
        cancel  = self.button (QMessageBox.StandardButton.Cancel)
        buttons = self.buttons()

        for button in buttons:
            if button:
                button.setFixedSize(40, 24)

        if  cancel:
            cancel.setFixedSize(60, 24)
            cancel.setStyleSheet("QPushButton {background: gray;}")
