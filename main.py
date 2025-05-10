#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1), Google-AI (Gemini)
#-----------------------------------------------------------------------------------------------------------------------

import sys
import logging
import weakref

from PyQt6.QtGui     import QFont
from PyQt6.QtCore    import pyqtSlot
from PyQt6.QtWidgets import QApplication

from gui.splash import SplashScreen
from util            import *
from gui.window      import Gui

# Application Subclass:
class Climact(QApplication):

    # Initializer
    def __init__(self, argv: list[weakref]):

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
        self.qss = "rss/style/macos.qss"
        self.setStyleSheet(read_qss(self.qss))
        self.setFont(QFont("Nunito", 14))
        logging.info(f"Application styled with {self.qss}")

        # Open splash-screen and show project options:
        self._init_gui()
        self._init_splash()

    # Open splash-screen:
    @pyqtSlot(name="Climact._init_splash")
    def _init_splash(self):

        # Initialize splash-screen:
        self.splash = SplashScreen()
        self.result = self.splash.exec()

        # Initialize GUI, open existing project if chosen:
        if self.result == 24:   self._init_gui(_open = False)
        if self.result == 25:   self._init_gui(_open = True)

    # Open main GUI:
    @pyqtSlot(name="Climact._init_gui")
    @pyqtSlot(bool, name="Climact._init_gui")
    def _init_gui(self, _open: bool = False):

        # Instantiate new GUI:
        self._gui = Gui()
        self._gui.sig_init_window.connect(self._init_splash)

        # Open project (if flag is set):
        if _open:   self._gui.open_project()

# Instantiate application and enter event-loop:
def main():
    _app = Climact(sys.argv)
    _app.exec()

if __name__ == "__main__":
    main()