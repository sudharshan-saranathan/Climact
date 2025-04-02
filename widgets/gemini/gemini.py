# System imports:
import os

from PyQt6.QtCore import QtMsgType
from PyQt6.QtWidgets import QMessageBox
from google import genai
from google.genai import types

from custom.message import Message

class Gemini:

    # Constructor:
    def __init__(self, model: str = "gemini-2.0-flash", *args, **kwargs):

        self.__api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.__enabled = bool(self.__api_key)

        # Open the instructions:
        with open("widgets/gemini/JSON-instructions.txt", 'r', encoding='utf-8') as file:
            self.__instructions = file.read()

        if not bool(self.__enabled):
            Message(
                QtMsgType.QtCriticalMsg,
                "Invalid environment variable: GOOGLE_AI_API_KEY",
                QMessageBox.StandardButton.Ok,
            )

        if not bool(self.__instructions):
            Message(
                QtMsgType.QtWarningMsg,
                "Genai-instructions are uninitialized. The assistant will offer limited help.",
                QMessageBox.StandardButton.Ok,
            )

        try:
            # Initialize generative AI:
            self.__genai_client = genai.Client(api_key=self.__api_key)
            self.__genai_stream = self.__genai_client.chats.create(model="gemini-2.0-flash")
            self.__genai_config = types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=self.__instructions,
            )

        except Exception as exception:
            print(f"INFO: An exception occurred: {exception}")
            print(f"AI - assistant has been disabled")
            self.__enabled = False

    def get_response(self, message: str):

        if not self.__enabled:
            return "AI-assistant has been disabled"

        response = self.__genai_stream.send_message(message, config=self.__genai_config)
        return response.text