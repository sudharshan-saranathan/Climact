from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import *

from custom.separator import Separator


class RadioButtonGroup(QFrame):

    def __init__(self, labels: list[str], parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Main widgets:
        self.__buttons = list()
        self.__group   = QButtonGroup(None)

        for label in labels:
            self.__button = QRadioButton(label)
            self.__button.setStyleSheet("QRadioButton {background: transparent;}")
            self.__buttons.append(self.__button)
            self.__group.addButton(self.__button)

        self.__buttons[0].setChecked(True)

        # Layout:
        __layout = QHBoxLayout(self)
        __layout.setContentsMargins(0, 0, 0, 0)
        __layout.setSpacing(8)

        for button in self.__buttons:
            __layout.addWidget(button)

        __layout.setStretch(2, 10)

class CostEditor(QLineEdit):

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Adjust style:
        self.setStyleSheet( "QLineEdit {"
                            "color          : black;"
                            "margin         : 0px;"
                            "border         : 1px solid black;"
                            "background     : white;" 
                            "border-radius  : 4px;"
                            "}")

class ObjectiveSetup(QFrame):

    # Initializer:
    def __init__(self, parent: QFrame | None):

        # Initialize base-class:
        super().__init__(parent)

        # Labels:
        self.__opttype = QLabel("<font color='lightslategray'>Opt Type</font>")
        self.__library = QLabel("<font color='lightslategray'>Library</font>")
        self.__cost_j1 = QLabel("<font color='lightslategray'>Cost (J1)</font>")
        self.__cost_j2 = QLabel("<font color='lightslategray'>Cost (J2)</font>")
        self.__cost_j3 = QLabel("<font color='lightslategray'>Cost (J3)</font>")

        # Radio Buttons:
        __button_scalarized = QRadioButton("Scalarized")
        __button_pareto     = QRadioButton("Pareto")
        __button_ampl     = QRadioButton("AMPL")
        __button_pymoo    = QRadioButton("Pymoo")
        __button_platypus = QRadioButton("Platypus")

        self.__group_1 = QButtonGroup(None)
        self.__group_2 = QButtonGroup(None)
        self.__group_1.addButton(__button_scalarized)
        self.__group_1.addButton(__button_pareto)
        self.__group_2.addButton(__button_ampl)
        self.__group_2.addButton(__button_pymoo)
        self.__group_2.addButton(__button_platypus)

        # Editor:
        self.__editor_1 = CostEditor(None)
        self.__editor_2 = CostEditor(None)
        self.__editor_3 = CostEditor(None)

        self.__choice_1 = RadioButtonGroup(["Maximize", "Minimize"], self)
        self.__choice_2 = RadioButtonGroup(["Maximize", "Minimize"], self)
        self.__choice_3 = RadioButtonGroup(["Maximize", "Minimize"], self)

        # Separator:
        __vline_left = QFrame()
        __vline_left.setFixedWidth(1)
        __vline_left.setFrameShape(QFrame.Shape.VLine)
        __vline_left.setStyleSheet("background: #efefef;")

        # Layout:
        __layout = QGridLayout(self)
        __layout.setHorizontalSpacing(8)
        __layout.setVerticalSpacing(6)
        __layout.setContentsMargins(0, 0, 0, 0)

        __layout.addWidget(self.__opttype, 0, 0)
        __layout.addWidget(__button_scalarized, 0, 2)
        __layout.addWidget(__button_pareto, 0, 3)
        __layout.addWidget(self.__library, 1, 0)
        __layout.addWidget(__button_ampl, 1, 2)
        __layout.addWidget(__button_pymoo, 1, 3)
        __layout.addWidget(__button_platypus, 1, 4)
        __layout.addWidget(self.__cost_j1 , 2, 0, Qt.AlignmentFlag.AlignLeft)
        __layout.addWidget(self.__cost_j2 , 3, 0, Qt.AlignmentFlag.AlignLeft)
        __layout.addWidget(self.__cost_j3 , 4, 0, Qt.AlignmentFlag.AlignLeft)
        __layout.addWidget(self.__library , 1, 0, Qt.AlignmentFlag.AlignLeft)
        __layout.addWidget(self.__editor_1, 2, 2, 1, 3)
        __layout.addWidget(self.__editor_2, 3, 2, 1, 3)
        __layout.addWidget(self.__editor_3, 4, 2, 1, 3)
        __layout.addWidget(self.__choice_1, 2, 5)
        __layout.addWidget(self.__choice_2, 3, 5)
        __layout.addWidget(self.__choice_3, 4, 5)
        __layout.setColumnStretch(4, 10)
        __layout.addWidget(__vline_left, 0, 1, 5, 1)

class TimeHorizon(QFrame):

    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Main-widgets:
        self.__label_1 = QLabel("Horizon: ")
        self.__label_2 = QLabel("Cadence: ")

        style = "QLineEdit {background: white; border: 1px solid black; border-radius: 4px;}"
        self.__input_1 = QLineEdit()
        self.__input_2 = QLineEdit()
        self.__input_1.setStyleSheet(style)
        self.__input_2.setStyleSheet(style)

        self.__input_1.setFixedWidth(30)
        self.__input_2.setFixedWidth(30)

        # Layout:
        __layout = QGridLayout(self)
        __layout.setContentsMargins(0, 0, 0, 0)
        __layout.setSpacing(2)

        __layout.addWidget(self.__label_1, 0, 0)
        __layout.addWidget(self.__label_2, 1, 0)
        __layout.addWidget(self.__input_1, 0, 1, Qt.AlignmentFlag.AlignLeft)
        __layout.addWidget(self.__input_2, 1, 1, Qt.AlignmentFlag.AlignLeft)

class Container(QFrame):

    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Adjust style:
        self.setContentsMargins(2, 2, 2, 2)

        # Main-widgets:
        self.__section   = QLabel("OPTIMIZATION SETTINGS")
        self.__horizon   = TimeHorizon(self)
        self.__objective = ObjectiveSetup(self)

        self.__hline_top = QFrame(None)
        self.__hline_mid = QFrame(None)

        self.__hline_top.setFrameShape(QFrame.Shape.HLine)
        self.__hline_mid.setFrameShape(QFrame.Shape.HLine)

        self.__hline_top.setFixedHeight(1)
        self.__hline_mid.setFixedHeight(1)

        self.__hline_top.setStyleSheet("QFrame {background: lightgray;}")
        self.__hline_mid.setStyleSheet("QFrame {background: lightgray;}")

        # Buttons:
        self.__run_button = QPushButton("Run Optimization")
        self.__gen_button = QPushButton("Generate script")
        self.__run_button.setEnabled(False)

        # Layout:
        __layout = QGridLayout(self)
        __layout.setContentsMargins(0, 0, 0, 0)
        __layout.setSpacing(2)

        __layout.addWidget(self.__section  , 0, 0)
        __layout.addWidget(self.__hline_top, 1, 0)
        __layout.addWidget(self.__objective, 2, 0)
        __layout.addWidget(self.__hline_mid, 3, 0)
        __layout.setRowStretch(4, 5)