# System imports:
import os
import time 

# Qt:
from PyQt6.QtCore import QtMsgType
from PyQt6.QtWidgets import QMessageBox

# Google, LangGraph:
from typing             import Dict, Any
from google             import genai
from google.genai       import types

from custom.dialog import Dialog

# Class Gemini: A wrapper that fetches responses from Google's Gemini API:
class Gemini:

    # Initializer:
    def __init__(self, model: str = "gemini-2.0-flash", *args, **kwargs):
        """
        Initializes the Gemini class.

        Args:
            model (str): The model to use for the Gemini API.
        """
        self._api_key = os.getenv("GOOGLE_API_KEY")     # Read API-key from environment variable
        self._enabled = bool(self._api_key)             # Check if API-key is defined
        self._prompts = None                            # Prompts for the assistant
        self._tokens = 0                                # Number of tokens generated

        # Open JSON-instructions for assistant:
        instructions = "tabs/gemini/JSON-instructions.txt"
        if os.path.exists(instructions):
            self._prompts = open(instructions, 'r').read()

        if not self._enabled:

            _dialog = Dialog(QtMsgType.QtCriticalMsg,
                             "Environment variable GOOGLE_API_KEY is undefined! The AI-assistant will be disabled",
                             QMessageBox.StandardButton.Ok
                             )
            _dialog.exec()

        if self._prompts is None:

            _dialog = Dialog(QtMsgType.QtWarningMsg,
                             "Genai-instructions are unavailable! Assistant will offer limited support.",
                             QMessageBox.StandardButton.Ok
                             )
            _dialog.exec()

        try:
            # Initialize generative AI:
            self._genai_client = genai.Client(api_key=self._api_key)
            self._genai_stream = self._genai_client.chats.create(model="gemini-2.5-pro-preview-05-06")
            self._genai_config = types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=self._prompts
            )

        except Exception as exception:
            print(f"INFO: An exception occurred: {exception}")
            print(f"AI - assistant has been disabled")
            self._enabled = False

    # Get response from Gemini:
    def get_response(self, _query: str, _json: str | None = None):
        """
        Get response from Gemini.

        Args:
            _query (str): The query to send to Gemini.
            _json (str | None): The JSON to send to Gemini.
        """

        # Disabled-check:
        if not self._enabled:   return "AI-assistant is disabled!"

        # Check if _json is a valid JSON string:
        if isinstance(_json, str):  _query =    f"{_query}\n\nThe following JSON-code describes " \
                                                 "the schematic currently displayed on the canvas:\n\n" \
                                                 "{_json}"
            
        else:   print(f"INFO: _json is None")

        # Fetch response from API, compute response-time:
        start = time.perf_counter()
        response = self._genai_stream.send_message(_query, 
                                                   config=self._genai_config
                                                   )
        final = time.perf_counter()

        # Get tokens generated:
        self._tokens +=  int(response.usage_metadata.total_token_count)

        # Print metadata:
        print(f"Response returned in {(final - start):.2f} seconds with "
              f"{response.usage_metadata.total_token_count} tokens"
              )

        return response.text