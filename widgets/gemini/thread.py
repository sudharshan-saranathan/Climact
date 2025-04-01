from re import compile, DOTALL

from PyQt6.QtCore import (QThread,
                          pyqtSignal)

from widgets.gemini.gemini import Gemini


class Thread(QThread):

    response_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, gemini: Gemini, message: str):
        super().__init__()

        self.gemini  = gemini
        self.message = message

    def run(self):

        try:
            response = self.gemini.get_response(self.message)
            match    = compile(r"```json\s*(.*?)\s*```", DOTALL).search(response)
            if match:
                print("JSON extracted")
                self.response_ready.emit(response, match.group(1))    # This sends the raw Json string

            else:
                self.response_ready.emit(response, "")

        except Exception as e:
            self.error_occurred.emit(str(e))



