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
                 _msg_type       : QtMsgType,
                 _msg_string     : str,
                 _default_button : QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
                 _default_parent : QWidget = None):

        # Initialize base-class:
        super().__init__(_default_parent)

        # Customize appearance and message:
        self.setWindowTitle(self.Attr.title)
        self.setFixedWidth (self.Attr.width)

        # Display message:
        self.setText(_msg_string)
        if _msg_type == QtMsgType.QtInfoMsg:
            self.setIcon(QMessageBox.Icon.Information)

        elif _msg_type == QtMsgType.QtWarningMsg:
            self.setIcon(QMessageBox.Icon.Warning)

        elif _msg_type == QtMsgType.QtCriticalMsg:
            self.setIcon(QMessageBox.Icon.Critical)

        elif _msg_type == QtMsgType.QtFatalMsg:
            self.setIcon(QMessageBox.Icon.Critical)

        # Default buttons:
        self.setStandardButtons(_default_button)

        # Customize the cancel-button:
        cancel  = self.button (QMessageBox.StandardButton.Cancel)
        buttons = self.buttons()

        # Set fixed-size for all buttons:
        [button.setFixedSize(40, 24) for button in buttons if button]

        # Distinguish the appearance of the cancel-button:
        if  cancel:
            cancel.setFixedSize(60, 24)
            cancel.setStyleSheet("QPushButton {background: gray;}")


    @staticmethod
    def standard_warning(_msg_string: str):

        # Initialize and display a warning-dialog:
        dialog = Dialog(QtMsgType.QtWarningMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()

    @staticmethod
    def standard_error(_msg_string: str):

        # Initialize and display an error-dialog:
        dialog = Dialog(QtMsgType.QtCriticalMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()

    @staticmethod
    def standard_critical(_msg_string: str):

        # Initialize and display a critical-dialog:
        dialog = Dialog(QtMsgType.QtCriticalMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()

    @staticmethod
    def standard_fatal(_msg_string: str):

        # Initialize and display a fatal-dialog:
        dialog = Dialog(QtMsgType.QtFatalMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()

    @staticmethod
    def standard_question(_msg_string: str):

        # Initialize and display a question-dialog:
        dialog = Dialog(QtMsgType.QtQuestionMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()

    @staticmethod
    def standard_information(_msg_string: str):

        # Initialize and display an information-dialog:
        dialog = Dialog(QtMsgType.QtInfoMsg, _msg_string)
        dialog.exec()

        # Return the dialog's result:
        return dialog.result()