"""
label.py
"""

# Standard library:
import types
import dataclasses

# PyQt6:
from PyQt6.QtCore import (
    Qt,
    pyqtSignal, QRectF
)
from PyQt6.QtGui import (
    QFont,
    QColor,
    QTextCursor, QPen, QBrush
)
from PyQt6.QtWidgets import (
    QStyle,
    QGraphicsItem,
    QGraphicsTextItem
)

# Class Label: A custom-QGraphicsTextItem
class String(QGraphicsTextItem):
    """
    A custom `QGraphicsTextItem` that allows for editable text labels in a graphics scene.
    """

    # Signals:
    sig_text_changed = pyqtSignal(str)

    # Initializer:
    def __init__(self, parent: QGraphicsItem | None, _text: str, **kwargs):

        # Initialize base-class:
        super().__init__(_text, parent)

        # Retrieve keywords:
        editable = kwargs.get("editable", True)                         # Text is editable by default
        font     = kwargs.get("font"    , QFont("Trebuchet MS", 12))    # Default font
        align    = kwargs.get("align"   , Qt.AlignmentFlag.AlignCenter) # Default alignment
        color    = kwargs.get("color"   , Qt.GlobalColor.black)         # Default text color
        width    = kwargs.get("width"   , 80)                           # Default text width

        # If bubble is enabled, draw a filled background:
        if  kwargs.get("bubble", False):
            self.pen = QPen(Qt.GlobalColor.black, 1.0)          # Pen for drawing bubble-border
            self.brs = QBrush(QColor(0xffffff))                 # Brush for the bubble's background

        # Customize attribute(s):
        try:
            option = self.document().defaultTextOption()
            option.setAlignment(align)
            self.document().setDefaultTextOption(option)

            self.setFont(font)              # Set font
            self.setTextWidth(width)        # Set text width
            self.setDefaultTextColor(color) # Set text color
            self.setTextInteractionFlags(   # Set text interaction flags
                Qt.TextInteractionFlag.TextEditorInteraction
                if editable else Qt.TextInteractionFlag.NoTextInteraction
            )

        except Exception as exception:
            print(exception)

    # Edit text:
    def edit(self):
        """
        Make the label editable by setting focus and selecting all text.
        """

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
        """
        Handle key-press events for the label. If the `Return` key is pressed, finish editing and clear focus.

        :param event:
        """
        # If the key pressed is `Return`, finish editing and clear focus:
        if event.key() == Qt.Key.Key_Return:
            self.clearFocus()
            event.accept()
            return

        # Otherwise, call super-class implementation:
        super().keyPressEvent(event)

    # Handle focus-out events:
    def focusOutEvent(self, event):
        """
        Handle focus-out events for the label. When focus is lost, emit a signal with the current text and toggle.
        :param event:
        """
        # Emit the text changed signal and clear selection:
        text = self.toPlainText()               # Get the current text
        self.textCursor().clearSelection()      # Clear text-selection
        self.sig_text_changed.emit(text)        # Notify listeners of text change

        # Super-class implementation:
        super().focusOutEvent(event)

    def paint(self, painter, option, widget):
        """
        Override the paint method to ensure the label does not have any state flags set.

        :param painter:
        :param option:
        :param widget:
        """
        # Remove the dashed-line appearance by setting the state to None:
        option.state = QStyle.StateFlag.State_None

        # If bubble is enabled, draw a filled-background:
        if (
            hasattr(self, 'pen') and
            hasattr(self, 'brs')
        ):
            painter.save()
            painter.setPen(self.pen)
            painter.setBrush(self.brs)
            painter.drawRoundedRect(QRectF(0, 0, self.textWidth(), self.boundingRect().height()), 5, 5)
            painter.restore()

        # Call the super-class implementation:
        super().paint(painter, option, widget)