from PyQt6.QtCore import QtMsgType, Qt
from PyQt6.QtWidgets    import (QWidget,
                                QMessageBox)

class Message(QMessageBox):

    # Default attribute(s):
    _title = "Dialog"
    _width =  500

    def __init__(self,
                 msg_type       : QtMsgType,
                 msg_string     : str,
                 default_button : QMessageBox.StandardButton = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                 default_parent : QWidget = None):

        # Initialize base-class:
        super().__init__(default_parent)

        # Customize appearance and message:
        self.setWindowTitle(self._title)
        self.setFixedWidth (self._width)

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

        # If the cancel button exists, change its style:
        if self.button(QMessageBox.StandardButton.Cancel):
            self.button(QMessageBox.StandardButton.Cancel).setStyleSheet("QPushButton {padding: 4px; background: darkgray; color: white;}")


