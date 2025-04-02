from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QSplitter, QGridLayout, QToolButton, QTextEdit, QLabel, QPushButton, QFrame
from PyQt6.QtCore    import Qt

from custom.separator import Separator
from widgets import Canvas
from widgets.optimize.objective import Container, TimeHorizon, ObjectiveSetup

class Optimizer(QWidget):

    def __init__(self, canvas: Canvas, parent: QWidget = None):

        # Initialize base-class:
        super().__init__(parent)

        # Editor style:
        style = ("QTextEdit {"
                 "border: none;"
                 "border-right: 1px solid white;"
                 "border-radius: 0px;"
                 "}")

        # Labels:
        self.__objective_setup = QLabel("OBJECTIVE SETUP", None)
        self.__t_horizon_setup = QLabel("TIME HORIZON", None)
        self.__objective_setup.setStyleSheet("QLabel {background: #cdcdcd;}")
        self.__t_horizon_setup.setStyleSheet("QLabel {background: #cdcdcd;}")

        # Main-widgets:
        self._editor = QTextEdit(self)
        self._result = QTextEdit(self)
        self._setup  = QWidget(self)

        self._result.setEnabled(False)
        self._editor.setStyleSheet(style)
        self._result.setStyleSheet(style)
        self._setup.setFixedWidth(600)

        # Separators:
        __hline_top = Separator(QFrame.Shape.HLine, None)
        __hline_mid = Separator(QFrame.Shape.HLine, None)
        __hline_bot = Separator(QFrame.Shape.HLine, None)

        # Buttons:
        self.__gen = QPushButton("Generate Script")
        self.__run = QPushButton("Optimize")
        self.__run.setEnabled(False)

        # Layout:
        self.__main_layout = QGridLayout(self)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)

        self.__main_layout.addWidget(self._setup , 0, 0, 2, 1)
        self.__main_layout.addWidget(self._editor, 0, 1)
        self.__main_layout.addWidget(self._result, 1, 1)

        # Sub-layout:
        self.__setup_layout = QGridLayout(self._setup)
        self.__setup_layout.setContentsMargins(8, 8, 8, 8)
        self.__setup_layout.setSpacing(12)

        self.__setup_layout.addWidget(QLabel("OPTIMIZATION SETUP"), 0, 0, 1, 4)
        self.__setup_layout.addWidget(ObjectiveSetup(None), 2, 0, 1, 4)
        self.__setup_layout.addWidget(Separator(QFrame.Shape.HLine, None, "lightgray"), 1, 0, 1, 4)
        self.__setup_layout.addWidget(Separator(QFrame.Shape.HLine, None, "lightgray"), 3, 0, 1, 4)
        self.__setup_layout.setRowStretch(4, 10)

        self.__setup_layout.addWidget(self.__gen, 5, 2)
        self.__setup_layout.addWidget(self.__run, 5, 3)
