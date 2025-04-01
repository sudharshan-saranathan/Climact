import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QShortcut,
                         QKeySequence)
from PyQt6.QtWidgets import (QFrame,
                             QTextEdit,
                             QVBoxLayout, QSizePolicy)

from widgets.gemini.gemini import Gemini
from widgets.gemini.thread import Thread
from widgets.schema.fileio import JsonLib


class Gui(QFrame):

    threads = []

    # Constructor:
    def __init__(self, canvas, parent = None):

        # Initialize base-class:
        super().__init__(parent)

        # Adjust style:
        self.setStyleSheet("QFrame {"
                           "border          : 2px solid black;"
                           "background      : white;"
                           "border-radius   : 8px;"
                           "}")

        # Create a layout to arrange child graph:
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        # Read-only text script that displays the GPT's response:
        self._canvas = canvas
        self._status = QFrame()
        self._window = QTextEdit()
        self._window.setReadOnly(True)
        self._window.setPlaceholderText("Hello! I'm an AI assistant. Ask me anything!")

        self._status.setFrameShape(QFrame.Shape.HLine)
        self._status.setFrameShadow(QFrame.Shadow.Raised)
        self._status.setFixedHeight(4)
        self._status.setStyleSheet("QFrame {"
                                   "border: 1px solid green;"
                                   "margin: 0px 150px 0px 150px;"
                                   "border-radius: 2px;"
                                   "background: green;"
                                   "}")

        # Text-script for querying:
        self._prompt = QTextEdit()
        self._prompt.setFixedHeight(80)
        self._prompt.setPlaceholderText("Type your query here!")

        # Customize appearance of text editors:
        self._window.setStyleSheet("color: black; background:transparent; border: none;")
        self._prompt.setStyleSheet("color: white; background:#44506C; border: none; border-radius: 7px;")
        self._prompt.setCursorWidth(8)

        # Install shortcut on the prompt:
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self._prompt)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.return_pressed)

        # Add editors to the layout:
        layout.addWidget(self._status)
        layout.addWidget(self._window)
        layout.addWidget(self._prompt)

        # Adjust graph-size and appearance:
        self.setFixedSize(500, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setContentsMargins(2, 2, 2, 2)
        self.gemini = Gemini()

    def return_pressed(self):

        if self._prompt.toPlainText() == "":
            return

        thread = Thread(self.gemini, self._prompt.toPlainText())

        # Notify user:
        self._window.setPlainText("The assistant is thinking...")
        self._prompt.clear()
        self._prompt.setEnabled(False)
        self._status.setStyleSheet("QFrame {"
                                   "border: 1px solid #ffab37;"
                                   "margin: 0px 150px 0px 150px;"
                                   "border-radius: 2px;"
                                   "background: #ffab37;"
                                   "}")

        thread.response_ready.connect(self.handle_response)
        thread.error_occurred.connect(self.handle_error)
        thread.finished.connect(lambda: self.threads.remove(thread))

        # Store thread:
        self.threads.append(thread)

        # Start the thread:
        thread.start()

    def handle_response(self, response: str, json_block: str):

        self._window.setMarkdown(response)
        self._prompt.setEnabled(True)
        self._status.setStyleSheet("QFrame {"
                                   "border: 1px solid green;"
                                   "margin: 0px 150px 0px 150px;"
                                   "border-radius: 2px;"
                                   "background: green;"
                                   "}")

        # Automatically make changes in the canvas:
        if bool(json_block):
            try:
                JsonLib.decode_json(json_block, self._canvas)

            except json.JSONDecodeError:
                pass

    def handle_error(self, error_msg: str):
        self._window.setMarkdown(error_msg)
        self._prompt.setEnabled(True)
        self._status.setStyleSheet("QFrame {"
                                   "border: 1px solid green;"
                                   "margin: 0px 200px 0px 200px;"
                                   "border-radius: 2px;"
                                   "background: green;"
                                   "}")

    def display_message(self, string: str):
        self._window.setPlainText(string)

