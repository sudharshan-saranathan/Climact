import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QStyle
from dataclasses import dataclass

# Class Label: A custom-QGraphicsTextItem
class Label(QGraphicsTextItem):

    # Signals:
    sig_text_changed = pyqtSignal(str, name="Label.sig_text_changed")

    @dataclass
    class Style:
        pen_border = Qt.PenStyle.NoPen
        background = Qt.BrushStyle.NoBrush

    # Initializer:
    def __init__(self, parent: QGraphicsItem | None, _text: str, **kwargs):

        # Initialize base-class:
        super().__init__(_text, parent)

        # Retrieve keywords:
        editable = kwargs["editable"]   if "editable"   in kwargs.keys() else True
        font     = kwargs["font"]       if "font"       in kwargs.keys() else QFont("Trebuchet MS", 13)
        align    = kwargs["align"]      if "align"      in kwargs.keys() else Qt.AlignmentFlag.AlignCenter
        color    = kwargs["color"]      if "color"      in kwargs.keys() else Qt.GlobalColor.black
        width    = kwargs["width"]      if "width"      in kwargs.keys() else 80

        # Customize attribute(s):
        try:
            option = self.document().defaultTextOption()
            option.setAlignment(align)
            self.document().setDefaultTextOption(option)

            self.editable = editable
            self.setFont(font)
            self.setTextWidth(width)
            self.setDefaultTextColor(color)
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction if editable else Qt.TextInteractionFlag.NoTextInteraction)

        except Exception as exception:
            logging.exception(f"An exception occurred: {exception}")
            pass

    # Edit text:
    def edit(self):

        # If not editable, return immediately:
        if not self.editable:   return

        # Make label editable:
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

        # Highlight text:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

    # Keyboard-event handler:
    def keyPressEvent(self, event):

        # If the key pressed is `Return`, finish editing and clear focus:
        if event.key() == Qt.Key.Key_Return:
            self.clearFocus()
            event.accept()
            return

        # Otherwise, call super-class implementation:
        super().keyPressEvent(event)

    # Handle focus-out events:
    def focusOutEvent(self, event):

        # Clear text-selection and emit signal:
        text = self.toPlainText()
        self.textCursor().clearSelection()      # Clear text-selection
        self.sig_text_changed.emit(text)        # Emit signal with new text as argument

        # Toggle editable:
        if not self.editable: self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        # Super-class implementation:
        super().focusOutEvent(event)

    def paint(self, painter, option, widget):
        option.state = QStyle.StateFlag.State_None
        super().paint(painter, option, widget)