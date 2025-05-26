from PyQt6.QtCore    import Qt
from PyQt6.QtWidgets import *
from custom.radiogroup import RadioButtonGroup

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
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Labels:
        self.__opttype = QLabel("<font color='lightslategray'>Opt Type</font>")
        self.__library = QLabel("<font color='lightslategray'>Library</font>")
        self.__cost_j1 = QLabel("<font color='lightslategray'>Cost (J1)</font>")
        self.__cost_j2 = QLabel("<font color='lightslategray'>Cost (J2)</font>")
        self.__cost_j3 = QLabel("<font color='lightslategray'>Cost (J3)</font>")

        # Radio Buttons:
        __button_scalar = QRadioButton("Scalarized")
        __button_pareto = QRadioButton("Pareto")
        __button_ampl   = QRadioButton("AMPL")
        __button_pymoo  = QRadioButton("Pymoo")
        __button_casadi = QRadioButton("Casadi")

        __button_casadi.setChecked(True)
        __button_scalar.setChecked(True)

        self.__group_1 = QButtonGroup(None)
        self.__group_2 = QButtonGroup(None)
        self.__group_1.addButton(__button_scalar)
        self.__group_1.addButton(__button_pareto)
        self.__group_2.addButton(__button_ampl)
        self.__group_2.addButton(__button_pymoo)
        self.__group_2.addButton(__button_casadi)

        # Editor:
        self.__editor_1 = CostEditor(None)
        self.__editor_2 = CostEditor(None)
        self.__editor_3 = CostEditor(None)

        self.__choice_1 = RadioButtonGroup(["Maximize", "Minimize"], self)
        self.__choice_2 = RadioButtonGroup(["Maximize", "Minimize"], self)
        self.__choice_3 = RadioButtonGroup(["Maximize", "Minimize"], self)

        # Separator:
        __vline_left = QFrame(self)
        __vline_left.setFixedWidth(1)
        __vline_left.setFrameShape(QFrame.Shape.VLine)
        __vline_left.setStyleSheet("background: #efefef;")

        # Layout:
        __layout = QGridLayout(self)
        __layout.setHorizontalSpacing(8)
        __layout.setVerticalSpacing(6)
        __layout.setContentsMargins(0, 0, 0, 0)

        __layout.addWidget(self.__opttype, 0, 0)
        __layout.addWidget(__button_scalar, 0, 2)
        __layout.addWidget(__button_pareto, 0, 3)
        __layout.addWidget(self.__library, 1, 0)
        __layout.addWidget(__button_ampl, 1, 2)
        __layout.addWidget(__button_pymoo, 1, 3)
        __layout.addWidget(__button_casadi, 1, 4)
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

    # Get objectives:
    def get_objectives(self):

        objectives = {
            self.__editor_1.text() : self.__choice_1.selected(),
            self.__editor_2.text() : self.__choice_2.selected(),
            self.__editor_3.text() : self.__choice_3.selected()
        }

        return objectives

    # Get checked opt-type:
    def get_opt_type(self) -> str:
        return self.__group_1.checkedButton().text()

    # Get checked buttons:
    def get_engine(self) -> str:
        return self.__group_2.checkedButton().text()