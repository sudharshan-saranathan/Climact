import re

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter
from PyQt6.QtWidgets import QTextEdit


class Editor(QTextEdit):

    # Signals:
    sig_validate_symbols = pyqtSignal(dict)
    sig_notify_config    = pyqtSignal(str)

    # Constructor:
    def __init__(self, parent):
        super().__init__(parent)

        self.setCursorWidth(8)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        accept = QShortcut(QKeySequence("Meta+Return"), self)
        accept.activated.connect(self.parse)

    def parse(self):

        equations = self.toPlainText().split('\n')
        symlist   = {}

        for equation in equations:

            equation = re.sub(r'([^\w\s.])', r' \1 ', equation)     # Add space around symbols
            equation = re.sub(r'\s+', ' ', equation).strip()        # Remove multiple spaces

            # Equation must have exactly 1 '=', it must not start or end with a '=':
            if  equation.count('=') == 1    and \
                not equation.endswith('=')  and \
                not equation.startswith('='):

                symbols = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', equation))
                symlist[equation] = symbols

            else:
                self.sig_notify_config.emit("ERROR: Equation has unrecognized format")

        if symlist:
            self.sig_validate_symbols.emit(symlist)

    def paintEvent(self, event):

        # Call base-class implementation:
        super().paintEvent(event)

        # draw cursor (if widget has focus)
        if self.hasFocus():
            rect = self.cursorRect(self.textCursor())
            painter = QPainter(self.viewport())
            painter.fillRect(rect, Qt.GlobalColor.white)

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Tab:
            return
        else:
            super().keyPressEvent(event)