#-----------------------------------------------------------------------------------------------------------------------
# Author    : Sudharshan Saranathan
# Year      : 2025
# GitHub    : https://github.com/sudharshan-saranathan/climact
# Module(s) : PyQt6 (version 6.8.1)
#-----------------------------------------------------------------------------------------------------------------------

import os, sys
import logging

from core.util       import *
from PyQt6.QtWidgets import QApplication

from gui.splash import SplashScreen
from gui.window      import Gui

class Climact(QApplication):

    # Global list of main-windows:
    windows = list()

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

        # Initialize stylesheet:
        self.qss = "rss/style/macos.qss"
        self.setStyleSheet(qss(self.qss))
        self.setFont(QFont("Nunito", 14))
        logging.info(f"Application styled with {self.qss}.")

        # Initialize splash-screen
        self._init_splash()

    # Splash-screen initializer:
    def _init_splash(self):

        # Instantiate splash-screen:
        self.splash = SplashScreen()
        self.result = self.splash.exec()

        if self.result == 24:   self._init_gui(_new = True)
        if self.result == 25:   self._init_gui(_new = False)

    @pyqtSlot(name="Climact.init_gui")
    def _init_gui(self, _new = True):
        _gui = Gui()                                    # Create a new GUI
        _gui.sig_init_window.connect(self._init_splash) # Connect the GUI's signal to this slot
        self.windows.append(_gui)                       # Store reference

        if not _new:    print(f"Opening schematic")

# Main:
def main():

    # Initialize and execute application:
    _app = Climact(sys.argv)
    _app.exec()

if __name__ == "__main__":
    main()