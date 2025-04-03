from PyQt6.QtCore import pyqtSignal, QObject
from amplpy import AMPL, AMPLException, OutputHandler, ErrorHandler

class AMPLOutput(OutputHandler):

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

class AMPLErrors(ErrorHandler):

    def __init__(self):
        self.__errors = list()

    def error(self, exception):
        self.__errors.append(exception)

    def get_error(self):
        return "".join(self.__errors)

class AMPLEngine:

    # Signals:
    sig_optimization_complete = pyqtSignal(str)

    # Initializer:
    def __init__(self):

        # Initialize base-class
        super().__init__()

        # Instantiate an AMPL engine:
        self.__ampl   = AMPL()
        self.__ampl.set_option("objective_precision", 3)
        self.__ampl.set_option("solution_precision" , 3)
        self.__ampl.set_option("display_precision"  , 3)

        self.__output = AMPLOutput()
        self.__errors = AMPLErrors()
        self.__ampl.setOutputHandler(self.__output)
        self.__ampl.setErrorHandler (self.__errors)

    # This function runs the AMPL optimization engine:
    def optimize(self, statements: str | None):

        if not bool(statements):
            return None

        try:
            self.__ampl.eval(statements)
            self.__ampl.solve(solver='ipopt', verbose=True)

            if self.__ampl.solve_result != 'solved':
                return None

            var_data = dict()
            par_data = dict()
            obj_data = dict()

            for var, var_entity in self.__ampl.get_variables():
                var_data[var] = var_entity.value()

            for par, par_entity in self.__ampl.get_parameters():
                par_data[par] = par_entity.value()

            for var, obj_entity in self.__ampl.get_objectives():
                obj_data[var] = obj_entity.value()

            return {"var_dict": var_data, "par_dict": par_data, "obj_dict": obj_data}

        except AMPLException as ampl_exception:
            self.__errors.error(str(ampl_exception))
            raise

    @property
    def output(self):
        return self.__output.get_history()

    @property
    def error(self):
        return self.__errors.get_error()