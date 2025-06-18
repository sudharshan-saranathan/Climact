#!/usr/bin/env python3
# encoding: utf-8
# splash.py
# ------------------------------------------------------------
# Date  : 2025-05-26
# Author: Sudharshan Saranathan
# Github: https://github.com/sudharshan-saranathan/climact.git
# ------------------------------------------------------------
"""
    climact.splash
    --------------
    This module defines a startup window for the Climact application, allowing users to choose between opening a blank project,
    loading a saved project, or viewing recent projects. The `StartupWindow` class inherits from `QDialog` and provides a
    user-friendly interface with buttons for each option. The window includes a logo and a title card, and it is designed to
    be displayed when the application starts.
"""
import types
import logging

from PyQt6.QtGui     import QIcon, QPixmap
from PyQt6.QtCore    import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)

from enum  import Enum
from util  import random_id

# StartupChoice enum:
class StartupChoice(Enum):
    """
    Enum representing the choices available in the startup window.
    """
    OPEN_BLANK_PROJECT = 1
    LOAD_SAVED_PROJECT = 2
    SHOW_RECENT        = 3

# Class StartupWindow: A QDialog subclass that is displayed on application startup:
class StartupWindow(QDialog):
    """
    A subclass of `QDialog` that appears at the start of the application, allowing users to choose between opening a
    blank project, loading a saved project, or viewing recent projects.
    """
    # Class constants:
    constants = types.SimpleNamespace(
        wsize = 400,
        hsize = 300,
    )

    # Class constructor:
    def __init__(self, parent: QWidget | None = None):
        super().__init__()

        # Customize attribute(s):
        self.setObjectName("Startup Window")
        self.setFixedSize(self.constants.wsize, self.constants.hsize)

        # Load logo and set window icon:
        logo, pixmap = QLabel(), QPixmap("rss/icons/logo.png").scaledToWidth(96, Qt.TransformationMode.SmoothTransformation)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(pixmap)

        # Title-card with icon and label:
        title = QLabel(
            """
            <div align="center">
                <span style="font-size:64pt; font-weight:600;">Climact</span><br>
                <span style="font-size:18pt;">Decarbonization Modeler</span>
            </div>
            """
        )

        top_layout = QHBoxLayout()      # Layout for arranging the logo and title:
        top_layout.addWidget(logo)
        top_layout.addWidget(title)

        # Add buttons:
        blank_project = QPushButton("Open Blank Project")   # Button to open a new blank project (Default choice)
        saved_project = QPushButton("Load Saved Project")   # Button to load a previously saved project
        show_recents  = QPushButton("Recent Projects")      # Button to show recent projects

        # Connect buttons to handlers:
        blank_project.pressed.connect(lambda: self.done(StartupChoice.OPEN_BLANK_PROJECT.value))
        saved_project.pressed.connect(lambda: self.done(StartupChoice.LOAD_SAVED_PROJECT.value))
        show_recents .pressed.connect(lambda: self.done(StartupChoice.SHOW_RECENT.value))

        # Arrange buttons in the startup-window:
        layout = QVBoxLayout(self)                  # Layout to arrange the `top_layout` and buttons vertically
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addLayout(top_layout)
        layout.addWidget(blank_project)
        layout.addWidget(saved_project)
        layout.addWidget(show_recents)