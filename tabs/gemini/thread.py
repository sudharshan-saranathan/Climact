from re import compile, DOTALL

from PyQt6.QtCore import QThread, pyqtSignal
from tabs.gemini  import gemini

class Thread(QThread):

    # Signals:
    response_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    # Initializer:
    def __init__(self, 
                _gemini: gemini.Gemini, 
                _msg: str,
                _json: str | None = None):
        """
        Initializes the Thread class.

        Args:
            _gemini (gemini.Gemini): The Gemini instance.
            _msg (str): The message to send to the Gemini API.
            _json (str | None): The JSON to send to the Gemini API.
        """
        super().__init__()

        self.gemini  = _gemini  # Gemini API instance (see gemini.py)
        self.schema  = _json    # JSON to send to the Gemini API
        self.message = _msg     # Message to send to the Gemini API

    def run(self):
        """
        Get response from Gemini.
        
        Parameters: None
        Returns: None
        """
        # Get response from Gemini:
        try:
            response =  self.gemini.get_response(self.message, self.schema)
            match    =  compile(r"```json\s*(.*?)\s*```", DOTALL).search(response)

            if  match:
                json_code = match.group(1)
                cresponse = response.replace(match.group(0), "").strip()
                self.response_ready.emit(cresponse, json_code)

                with open("dump.json", "w") as _file:
                    _file.write(json_code)

            else:
                self.response_ready.emit(response, None)

        except Exception as exception:  self.error_occurred.emit(str(exception))



