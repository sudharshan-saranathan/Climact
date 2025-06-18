#!/usr/bin/env python3
# encoding: utf-8
# main.py
"""
    climact.main
    ------------
    This module serves as the entry point for the Climact application, initializing the main application class and
    starting the event loop. It initializes the application with command-line arguments, sets up logging, and defines
    additional constants such as the stylesheet and font size. The main function creates an instance of the Climact
    application and enters the event loop.

    Usage:
        python main.py [options]
"""

__author__  = "Sudharshan Saranathan"
__version__ = "0.1.0"
__license__ = "None"
__date__    = "2025-05-26"

# Imports:
import sys
import types
import logging
import argparse
import platform

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from gui  import *
from util import *

# Application Subclass:
class Climact(QApplication):
    """
    The main application class for Climact, inherits from QApplication.
    """

    # Application-level constants:
    constants = types.SimpleNamespace(
        QSS_SHEET = "rss/style/default.qss",
        FONT_SIZE = 11 if platform.system() == "Windows" else 14  # Default font size,
    )

    # Class constructor:
    def __init__(self, argv: list):
        super().__init__(argv)      # Initialize the QApplication with

        # Set up a parser for command-line arguments:
        parser = argparse.ArgumentParser(description="Climact: Decarbonization Simulation Platform")
        parser.parse_args()

        # Define logging-behaviour:
        logging.basicConfig(
            filename='climact.log',
            filemode='w',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s'
        )

        # Initialize stylesheet, set font:
        self.setFont(QFont("Trebuchet MS", self.constants.FONT_SIZE))
        self.setStyleSheet(read_qss (self.constants.QSS_SHEET))
        logging.info(f"Stylesheet: {self.constants.QSS_SHEET}")

        # Open the splash-screen and show project options:
        self._window  = Gui()
        self._startup = StartupWindow()
        self._result  = self._startup.exec()

        # If the user chooses to load a saved project, call the import method:
        if  self._result == StartupChoice.LOAD_SAVED_PROJECT.value:
            self._window.import_project()

# Instantiate application and enter event-loop:
def main():
    """
    Main function to start the Climact application.
    """
    _app = Climact(sys.argv)
    _app.exec()

if __name__ == "__main__":
    main()