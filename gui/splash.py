from PyQt6.QtGui     import QPixmap
from PyQt6.QtCore    import Qt
from PyQt6.QtWidgets import (QDialog,
                             QLabel,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout)

from enum import Enum
from util import random_id

# StartupChoice enum:
class StartupChoice(Enum):
    OPEN_BLANK_PROJECT = 1
    LOAD_SAVED_PROJECT = 2
    SHOW_RECENT        = 3

# Class StartupWindow: A QDialog subclass that is displayed on application startup:
class StartupWindow(QDialog):

    # Constants:
    class Constants:
        WINDOW_WIDTH  = 400
        WINDOW_HEIGHT = 300

    # Initializer:
    def __init__(self):

        # Initialize super-class:
        super().__init__()

        # Customize attribute(s):
        self.setObjectName("Startup Window")
        self.setFixedSize(self.Constants.WINDOW_WIDTH, self.Constants.WINDOW_HEIGHT)

        # Load logo and
        logo, pixmap = QLabel(), QPixmap("rss/icons/logo.png").scaledToWidth(96)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(pixmap)

        # Title-card with icon and label:
        title = QLabel(
            """
            <div align="center">
                <span style="font-size:64pt; font-weight:600;">Climact</span><br>
                <span style="font-size:16pt;">Decarbonization Modeler</span>
            </div>
            """
        )

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(title)

        # Add buttons:
        blank_project = QPushButton("Open Blank Project")
        saved_project = QPushButton("Load Saved Project")
        show_recents  = QPushButton("Recent Projects")

        # Connect buttons to handlers:
        blank_project.pressed.connect(lambda: self.done(StartupChoice.OPEN_BLANK_PROJECT.value))
        saved_project.pressed.connect(lambda: self.done(StartupChoice.LOAD_SAVED_PROJECT.value))
        show_recents.pressed .connect(lambda: self.done(StartupChoice.SHOW_RECENT.value))

        # Arrange buttons in startup-window:
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(blank_project)
        layout.addWidget(saved_project)
        layout.addWidget(show_recents)