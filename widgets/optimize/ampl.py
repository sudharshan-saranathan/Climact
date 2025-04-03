from PyQt6.QtCore import pyqtSignal, QObject
from amplpy import AMPL, AMPLException, OutputHandler

class Handler(OutputHandler):

    def __init__(self):
        self.__output  = None
        self.__history = list()

    def output(self, kind, msg):
        self.__output = msg
        self.__history.append(msg)

    def get_output(self):
        return self.__output

    def get_history(self):
        return "".join(self.__history)

class AMPLEngine:

    # Signals:
    sig_optimization_complete = pyqtSignal(str)

    # Initializer:
    def __init__(self):

        # Initialize base-class
        super().__init__()

        # Instantiate an AMPL engine:
        self.__ampl    = AMPL()
        self.__handler = Handler()
        self.__ampl.setOutputHandler(self.__handler)

    # This function runs the AMPL optimization engine:
    def optimize(self, statements: str | None):

        if not bool(statements):
            return

        try:
            self.__ampl.eval(statements)
            self.__ampl.solve(solver='ipopt', verbose=True)
            print(f"INFO: AMPL Solve Output: {self.__ampl.solve_result}")

        except AMPLException as ampl_exception:
            print(f"ERROR: {ampl_exception}")

        except Exception as exception:
            print(f"ERROR: {exception}")

    @property
    def output(self):
        return self.__handler.get_history()