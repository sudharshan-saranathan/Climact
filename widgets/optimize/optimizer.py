from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QSplitter, QGridLayout, QToolButton, QTextEdit, QLabel, QPushButton, QFrame, \
    QStackedWidget, QTabBar, QTabWidget
from PyQt6.QtCore    import Qt
from amplpy import AMPLException

from custom.separator import Separator
from widgets import Canvas
from widgets.optimize.ampl import AMPLEngine
from widgets.optimize.objective import Container, TimeHorizon, ObjectiveSetup
from widgets.schema.graph import Stream


class Optimizer(QWidget):

    # Global sets:
    pars_set = set()
    vars_set = set()
    eqns_set = set()

    # Global dictionaries:
    var_dict = dict()       # Dictionary to retrieve the handle's reference using symbol
    par_dict = dict()       # Dictionary to retrieve the parameter's reference using symbol

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
        self.__setup_layout.addWidget(ObjectiveSetup(None), 2, 0, 1, 4)
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

        # Clear the editor:
        self._editor.clear()

        ecount = 0
        prefix = "# AMPL Optimization\n"

        _var_decl = "# Variable(s):\n"
        _eqn_decl = "# Equation(s):\n"
        _par_decl = "# Parameter(s):\n"

        for node in self.__canvas.nodes:

            _vars = node[Stream.INP] + node[Stream.OUT]
            _pars = node[Stream.PAR]
            _prfx = node.nuid().replace('#', '', 1)     # Remove the '#' from the node-id

            for var in _vars:

                # If the handle is not connected, skip:
                if not var.connected:
                    continue

                # If the variable has a fixed value, declare it as a parameter instead:
                if var.value is not None:
                    _par_decl = _par_decl + f"param {var.connector.symbol}\t\t= {str(var.value)};\n"
                    self.pars_set.add(var.symbol)

                # Otherwise, declare the connector's symbol as a variable:
                elif var.connector.symbol not in self.vars_set:
                    _var_decl = _var_decl + f"var {var.connector.symbol};\n"
                    self.vars_set.add(var.connector.symbol)

                # Create a dictionary-map:
                self.var_dict[var.connector.symbol] = var

            for par in _pars:

                # Conversely, if the parameter's value is undefined, declare it as a variable:
                if par.value is None:
                    _var_decl = _var_decl + f"var {_prfx}_{par.symbol};\n"

                # Parameter declaration:
                else:
                    _par_decl = _par_decl + f"param {_prfx}_{par.symbol}\t= {par.value};\n"

                # Store in map:
                self.par_dict[par.symbol] = par

            for equation in node.substituted:
                _eqprefix = f"subject to equation_{ecount}"
                _eqn_decl = _eqn_decl + f"{_eqprefix}: {equation};\n"
                ecount = ecount + 1

        script = f"{prefix}\n{_par_decl}\n{_var_decl}\n{_eqn_decl}"
        self._editor.setText(script)

    def run(self):

        try:
            engine = AMPLEngine()
            result = engine.optimize(self._editor.toPlainText())
            output = str()

            if result:
                for key in result["var_dict"].keys():
                    output += f"{key}\t= {result["var_dict"][key]}\n"

                for key in result["par_dict"].keys():
                    output += f"{key}\t= {result["par_dict"][key]}\n"

                for key in result["obj_dict"].keys():
                    output += f"{key}\t= {result["obj_dict"][key]}\n"

                self._result.setText(output)

        except Exception as exception:

            # Log to application:
            self._result.setText(f"Exception: {str(exception)}")

        self._tabwid.setCurrentWidget(self._result)

    def auto_enable(self):

        if bool(self._editor.toPlainText()):
            self.__run.setEnabled(True)

        else:
            self.__run.setEnabled(False)