from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QFrame

# Splash Screen
class SplashScreen(QDialog):

    # Instance Initializer:
    def __init__(self):

        # Initialize super-class:
        super().__init__()

        # Customize attribute(s):
        self.setFixedSize(400, 300)
        self.setStyleSheet("QDialog {background: #efefef;}")

        logo, pixmap = QLabel(), QPixmap("rss/icons/logo.png").scaledToWidth(96, Qt.TransformationMode.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        new_project = QPushButton("Blank Project")
        exs_project = QPushButton("Open Existing")
        recent_list = QPushButton("Recent Projects")

        # Connect buttons to handlers:
        new_project.pressed.connect(lambda: self.done(24))
        exs_project.pressed.connect(lambda: self.done(25))

        # Arrange UI elements in layout:
        layout = QVBoxLayout(self)
        layout.addLayout(top_layout)
        layout.addWidget(new_project)
        layout.addWidget(exs_project)
        layout.addWidget(recent_list)

    # Handle choice `New Project`:
    def open_new(self):
        self.done(24)
        self.accept()

    # Handle choice `Open Project`:
    def open_exs(self):
        self.done(25)
        self.accept()



