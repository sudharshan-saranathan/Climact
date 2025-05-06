from re import compile, DOTALL

from PyQt6.QtCore import QThread, pyqtSignal
from tabs.gemini  import gemini

class Thread(QThread):

    response_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, _gemini: gemini.Gemini, _msg: str):
        super().__init__()

        self.gemini  = _gemini
        self.message = _msg

    def run(self):

        """
        llm_prompt   = {"prompt": self.message}
        llm_response = app.invoke(llm_prompt)

        # Concatenate response:
        steps = llm_response['graph']['nodes']
        process_description = "\n".join(step["label"] for step in steps)

        # Emit signal
        self.response_ready.emit(process_description, None)
        """

        try:
            response =  self.gemini.get_response(self.message)
            match    =  compile(r"```json\s*(.*?)\s*```", DOTALL).search(response)

            with open('dump.json', 'w+') as f:
                f.write(match.group(1))

            if match:
                json_code = match.group(1)
                cresponse = response.replace(match.group(0), "").strip()
                self.response_ready.emit(cresponse, json_code)

            else:
                self.response_ready.emit(response, None)

        except Exception as e:
            self.error_occurred.emit(str(e))



