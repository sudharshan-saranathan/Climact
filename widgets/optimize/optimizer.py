from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QSplitter, QGridLayout, QToolButton, QTextEdit, QLabel, QPushButton, QFrame, \
    QStackedWidget, QTabBar, QTabWidget
from PyQt6.QtCore import Qt, pyqtSignal
from amplpy import AMPLException

from custom.separator import Separator
from widgets import Canvas
from widgets.optimize.ampl import AMPLEngine
from widgets.optimize.objective import ObjectiveSetup
from widgets.schema.graph import Stream, Connector, Handle


class Optimizer(QWidget):

    # Signals:
    sig_modify_connectors = pyqtSignal(dict)

    # Global dictionaries:
    var_dict = dict()       # Dictionary to retrieve the handle's reference using symbol
    par_dict = dict()       # Dictionary to retrieve the parameter's reference using symbol
    entity_map = dict()

    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget = None):

        # Initialize base-class:
        super().__init__(parent)

        # Store the canvas' reference:
        self.__canvas = canvas

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
        self._tabwid = QTabWidget(self)
        self._wstack = QStackedWidget(self)
        self._editor = QTextEdit(self)
        self._result = QTextEdit(self)
        self._setup  = QWidget(self)
        self._obj    = ObjectiveSetup(None)

        self._tabwid.setTabPosition(QTabWidget.TabPosition.North)
        self._editor.setStyleSheet(style)
        self._result.setStyleSheet(style)
        self._setup.setFixedWidth(600)

        # Organize tab-widget:
        self._tabwid.addTab(self._editor, "Model")
        self._tabwid.addTab(self._result, "Log")
        self._tabwid.addTab(QWidget(), "Analysis")

        # Separators:
        __hline_top = Separator(QFrame.Shape.HLine, None)
        __hline_mid = Separator(QFrame.Shape.HLine, None)
        __hline_bot = Separator(QFrame.Shape.HLine, None)

        # Buttons:
        self.__gen = QPushButton("Generate Script")
        self.__run = QPushButton("Optimize")
        self.__run.setEnabled(False)
        self.__gen.pressed.connect(self.generate)
        self.__run.pressed.connect(self.run)

        # Layout:
        self.__main_layout = QGridLayout(self)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)

        self.__main_layout.addWidget(self._setup , 0, 0, 3, 1)
        self.__main_layout.addWidget(self._tabwid, 0, 1, 3, 1)

        # Sub-layout:
        self.__setup_layout = QGridLayout(self._setup)
        self.__setup_layout.setContentsMargins(8, 8, 8, 8)
        self.__setup_layout.setSpacing(12)

        self.__setup_layout.addWidget(QLabel("OPTIMIZATION SETUP"), 0, 0, 1, 4)
        self.__setup_layout.addWidget(self._obj, 2, 0, 1, 4)
        self.__setup_layout.addWidget(Separator(QFrame.Shape.HLine, None, "lightgray"), 1, 0, 1, 4)
        self.__setup_layout.addWidget(Separator(QFrame.Shape.HLine, None, "lightgray"), 3, 0, 1, 4)
        self.__setup_layout.addWidget(self._wstack, 4, 0, 1, 4)
        self.__setup_layout.setRowStretch(5, 10)

        self.__setup_layout.addWidget(self.__gen, 5, 2)
        self.__setup_layout.addWidget(self.__run, 5, 3)

        # Signal-slot connections:
        self._editor.textChanged.connect(self.auto_enable)

    # Generates an AMPL script:
    def generate(self):

        # Clear editor:
        self._editor.clear()

        var_set = set()
        par_set = set()

        self.par_dict.clear()
        self.var_dict.clear()
        self.entity_map.clear()

        ecount = 0
        ocount = 0
        scr_prfx = "# AMPL Optimization\n"
        eqn_prfx = f"subject to equation_"

        # Sections:
        var_section = "# Variable(s):\n"
        eqn_section = "# Equation(s):\n"
        obj_section = "# Objective(s):\n"
        par_section = "# Parameter(s):\n"

        for node in self.__canvas.nodes:
            var_list = node.variables()
            par_list = node[Stream.PAR]
            n_prefix = node.nuid().replace('#', '', 1)     # Remove '#' from the node-id

            for variable in var_list:

                # Convenience variable:
                symbol = variable.connector.symbol
                self.entity_map[symbol] = variable

                # If the variable is already declared, skip processing:
                if variable.connector.symbol in var_set | par_set:
                    continue

                # Declare variable (as a parameter if its value is defined):
                if isinstance(variable.value, float):
                    par_set.add(symbol)
                    par_section += f"param {symbol} = {variable.value};\n"

                else:
                    var_set.add(symbol)
                    var_section += f"var {symbol};\n"

                    # If bounds are provided, add them as equations:
                    if isinstance(variable.lower, float):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {variable.lower} >= 0.0;\n"
                        ecount += 1

                    if isinstance(variable.upper, float):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {variable.upper} <= 0.0;\n"
                        ecount += 1

            for parameter in par_list:

                # Convenience variable:
                symbol = f"{n_prefix}_{parameter.symbol}"
                self.entity_map[symbol] = parameter

                # If parameter has already been declared, skip processing:
                if symbol in var_set | par_set:
                    continue

                # If the parameter doesn't have a value, declare it as a variable
                if isinstance(parameter.value, float):
                    par_set.add(symbol)
                    par_section += f"param {symbol} = {parameter.value};\n"

                else:
                    var_set.add(symbol)
                    var_section += f"var {symbol};\n"

                    # If bounds are provided, add them as equations:
                    if isinstance(parameter.lower, float):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {parameter.lower} >= 0.0;\n"
                        ecount += 1

                    if isinstance(parameter.upper, float):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {parameter.upper} <= 0.0;\n"
                        ecount += 1

            for equation in node.substituted:
                eqn_section += f"{eqn_prfx}{ecount}: {equation};"
                ecount += 1

        dictionary = self._obj.get_objectives()
        objectives = dictionary.keys()

        for objective in objectives:
            if bool(objective):
                obj_section += f"{dictionary[objective].lower()} obj_{ocount}: {objective};\n"
                ocount    += 1

        script = f"{scr_prfx}\n{par_section}\n{var_section}\n{obj_section}\n{eqn_section}"
        self._editor.setText(script)

    def run(self):

        engine = AMPLEngine()
        result = engine.optimize(self._editor.toPlainText())

        self._result.setText(f"AMPL Result: [{engine.result}]")
        self._result.append ("-" * 36)

        if engine.result == "solved":

            output = str()
            for key in result["var_dict"].keys():
                output += f"{key}\t= {result["var_dict"][key]}\n"
                # if isinstance(self.entity_map[key], Handle):
                #     self.entity_map[key].connector.thickness = int(result["var_dict"][key])

            for key in result["par_dict"].keys():
                output += f"{key}\t= {result["par_dict"][key]}\n"
                # if isinstance(self.entity_map[key], Handle):
                #     self.entity_map[key].connector.thickness = int(result["var_dict"][key])

            for key in result["obj_dict"].keys():
                output += f"{key}\t= {result["obj_dict"][key]}\n"

            self._result.append(output)
            self.sig_modify_connectors.emit(result)

        else:
            self._result.append(engine.error)

        self._tabwid.setCurrentWidget(self._result)

    def auto_enable(self):

        if bool(self._editor.toPlainText()):
            self.__run.setEnabled(True)

        else:
            self.__run.setEnabled(False)