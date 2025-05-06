# System imports:
import os

# Qt:
from PyQt6.QtCore import QtMsgType
from PyQt6.QtWidgets import QMessageBox

# Google, LangGraph:
from typing             import Dict, Any
from google             import genai
from google.genai       import types

from core.dialog import Dialog

# Class Gemini: A wrapper that fetches responses from Google's Gemini API:
class Gemini:

    # Constructor:
    def __init__(self, model: str = "gemini-2.0-flash", *args, **kwargs):

        self._api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not bool(self._api_key):
            self._api_key = "AIzaSyAPC-Jd-LTQDMUYhLZGeB03jJulDlrt5fk"

        self._enabled = bool(self._api_key)
        self._instructions = None
        self._tokens = 0

        # Open JSON-instructions for assistant:
        try:
            with open("tabs/gemini/JSON-instructions.txt", 'r', encoding='utf-8') as file:
                self._instructions = file.read()

        except FileNotFoundError:
            pass

        if not bool(self._enabled):
            _dialog = Dialog(QtMsgType.QtCriticalMsg,
                             "Invalid environment variable: GOOGLE_AI_API_KEY",
                             QMessageBox.StandardButton.Ok
                             )
            _dialog.exec()

        if self._instructions is None:
            _dialog = Dialog(QtMsgType.QtWarningMsg,
                             "Genai-instructions are unavailable! Assistant will offer limited support.",
                             QMessageBox.StandardButton.Ok
                             )
            _dialog.exec()

        try:
            # Initialize generative AI:
            self._genai_client = genai.Client(api_key=self._api_key)
            self._genai_stream = self._genai_client.chats.create(model="gemini-1.5-pro")
            self._genai_config = types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=self._instructions,
            )

        except Exception as exception:
            print(f"INFO: An exception occurred: {exception}")
            print(f"AI - assistant has been disabled")
            self._enabled = False

    # Get response from Gemini:
    def get_response(self, query: str):

        # Disabled-check:
        if not self._enabled:   return "AI-assistant is disabled!"

        # Fetch response from API:
        response = self._genai_stream.send_message(query, config=self._genai_config)
        self._tokens +=  int(response.usage_metadata.total_token_count)

        print(f"Tokens generated for latest prompt: {response.usage_metadata.total_token_count}")
        print(f"Tokens generated in total: {self._tokens}")

        return response.text