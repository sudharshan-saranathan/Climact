from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QGridLayout, QTextEdit, QLabel, QPushButton, QFrame, QStackedWidget, QTabWidget

from custom.entity import EntityClass, EntityState
from custom.separator import Separator

from tabs.optima.ampl import AMPLEngine
from tabs.optima.objective import ObjectiveSetup
from tabs.schema.canvas import Canvas


class Optimizer(QWidget):

    # Signals:
    sig_modify_connectors = pyqtSignal(dict)

    # Initializer:
    def __init__(self, canvas: Canvas, parent: QWidget = None):

        # Initialize base-class:
        super().__init__(parent)

        # Dictionaries:
        self.var_dict   = dict()
        self.par_dict   = dict()
        self.entity_map = dict()

        # Store the canvas' reference:
        self._canvas = canvas

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

        for terminal, state in self._canvas.term_db.items():

            # Skip unconnected terminals or hidden terminals::
            if (
                not bool(terminal.socket.label) or 
                not terminal.socket.connected or
                not state
            ):  
                continue

            # Define entity name:
            entity_name = f"TOTAL_{terminal.socket.label}"

            # Define total-flow variable:
            if (
                    entity_name not in var_set and
                    entity_name not in par_set
            ):

                if bool(terminal.socket.value): # If value is provided, define entity as parameter

                    par_section = f"param TOTAL_{terminal.socket.label} = {terminal.socket.value};\n"
                    par_set.add(entity_name)

                    # Map variable name to entity:
                    self.entity_map[entity_name] = terminal.socket

                else:   # Define as variable

                    var_section += f"var {entity_name};\n"
                    var_set.add(entity_name)

                    # Map variable name to entity:
                    self.entity_map[entity_name] = terminal.socket

                    # group, equation = self._canvas.group_flows(terminal.socket.label, generate_eqn = True)
                    # eqn_section += f"{eqn_prfx}{ecount}: {equation}\n"
                    #ecount += 1

        for node, state in self._canvas.node_db.items():

            # Skip hidden nodes:
            if not state: continue

            n_prefix = node.uid
            var_list = [
                variable for variable, state in node[EntityClass.VAR].items() 
                if state == EntityState.ACTIVE
            ]

            par_list = [
                parameter for parameter, state in node[EntityClass.PAR].items()
                if state == EntityState.ACTIVE
            ]

            print(f"Node has {len(var_list)} variables and {len(par_list)} parameters")

            for variable in var_list:

                # Null-check:
                if variable.connector is None:  continue

                symbol = variable.connector().symbol
                self.entity_map[symbol] = variable

                # If the variable is already declared, skip processing:
                if  symbol in var_set | par_set:
                    continue

                # Declare variable (as a parameter if its value is defined):
                if  bool(variable.value):
                    par_set.add(symbol)
                    par_section += f"param {symbol} = {variable.value};\n"

                else:
                    var_set.add(symbol)
                    var_section += f"var {symbol};\n"

                    # If bounds are provided, add them as equations:
                    if  bool(variable.minimum):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {variable.minimum} >= 0.0;\n"
                        ecount += 1

                    if  bool(variable.maximum):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {variable.maximum} <= 0.0;\n"
                        ecount += 1

            for parameter in par_list:

                # Convenience variable:
                symbol = f"{n_prefix}_{parameter.symbol}"
                self.entity_map[symbol] = parameter

                # If parameter has already been declared, skip processing:
                if symbol in var_set | par_set:
                    continue

                # If the parameter doesn't have a value, declare it as a variable
                if  bool(parameter.value):
                    par_set.add(symbol)
                    par_section += f"param {symbol} = {parameter.value};\n"

                else:
                    var_set.add(symbol)
                    var_section += f"var {symbol};\n"

                    # If bounds are provided, add them as equations:
                    if  bool(parameter.minimum):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {parameter.minimum} >= 0.0;\n"
                        ecount += 1

                    if  bool(parameter.maximum):
                        eqn_section += f"{eqn_prfx}{ecount}: {symbol} - {parameter.maximum} <= 0.0;\n"
                        ecount += 1

            for equation in node.substituted():
                eqn_section += f"{eqn_prfx}{ecount}: {equation};\n"
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

            for key in result["par_dict"].keys():
                output += f"{key}\t= {result["par_dict"][key]}\n"

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