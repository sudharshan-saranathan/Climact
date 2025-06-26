#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------

import sys
import logging
import platform

from PyQt6.QtGui     import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from gui.splash import StartupWindow, StartupChoice
from util            import *
from gui.window      import Gui

# Application Subclass:
class Climact(QApplication):

    # Constants:
    class Metadata:
        APP_NAME    = "Climact"
        APP_LOGO    = "rss/icons/logo.png"
        APP_VERSION = "0.1.0"
        APP_AUTHOR  = "Sudharshan Saranathan"
        APP_GITHUB  = "https://github.com/sudharshan-saranathan/climact"
        APP_MODULES = "PyQt6, Google-AI (Gemini)"

    class Constants:
        QSS_SHEET = "rss/style/macos.qss"
        FONT_SIZE = 14 if platform.system() == "Darwin" else 9  # Adjust font size for macOS

    # Initializer
    def __init__(self, argv: list):

        # Initialize super-class:
        super().__init__(argv)

        # Define logging-behaviour:
        logging.basicConfig(
            filename='climact.log',
            filemode='w',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s'
        )

        # Initialize stylesheet, set font:
        self.setFont(QFont("Trebuchet MS", self.Constants.FONT_SIZE))
        self.setStyleSheet(read_qss (self.Constants.QSS_SHEET))
        logging.info(f"Stylesheet: {self.Constants.QSS_SHEET}")

        # Open the splash-screen and show project options:
        self._window  = Gui()
        self._startup = StartupWindow()
        self._result  = self._startup.exec()

        if  self._result == StartupChoice.LOAD_SAVED_PROJECT.value:
            self._window.load_project()
            

# Instantiate application and enter event-loop:
def main():
    _app = Climact(sys.argv)
    _app.exec()

if __name__ == "__main__":
    main()