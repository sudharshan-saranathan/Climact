from amplpy import AMPL, AMPLException, Environment

class AMPLEngine:

    # Initializer:
    def __init__(self):

        # Initialize base-class
        super().__init__()

        # Instantiate an AMPL engine:
        self.__ampl = AMPL()