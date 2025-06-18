"""
maps.py
-------
This module defines a `Maps` widget that displays Google Maps using PyQt6's QWebEngineView.
"""

import sys
import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineSettings # Import QWebEngineSettings

class Maps(QWidget):
    """
    Maps widget that displays a Google Map using PyQt6's QWebEngineView.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Maps in PyQt6")
        self.setGeometry(100, 100, 800, 600)

        self.browser = QWebEngineView(None)
        self.layout  = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.browser)

        # --- IMPORTANT SETTINGS FOR LOCAL HTML and EXTERNAL JS ---
        # 1. Enable JavaScript (usually on by default, but good to be explicit)
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # 2. Allow local content to access remote URLs (Crucial for Google Maps API)
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # 3. Allow local content to access file URLs (if your HTML references local assets like images/CSS)
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        # (Optional but Recommended) Allow running insecure content if you encounter mixed content issues
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        # --------------------------------------------------------

        path = os.path.abspath("tabs/maps/maps.html")
        self.browser.load(QUrl.fromLocalFile(path))

        # Option 2: Load directly with setHtml() (less reliable for external scripts)
        # self.browser.setHtml(html_content, baseUrl=QUrl.fromLocalFile(os.path.abspath(os.path.dirname(__file__)) + "/"))