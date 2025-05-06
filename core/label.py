from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QStyle

from dataclasses import dataclass

class Label(QGraphicsTextItem):

    # Signals:
    sig_text_changed = pyqtSignal(str, name="Text Changed")

    @dataclass
    class Style:
        pen_border = Qt.PenStyle.NoPen
        background = Qt.BrushStyle.NoBrush

    # Initializer:
    def __init__(self, parent: QGraphicsItem | None, **kwargs):

        # Initialize base-class:
        super().__init__(parent)

        # Get keyword-attribute(s):
        edit  = kwargs.get("edit")  if "edit"  in kwargs else True
        font  = kwargs.get("font")  if "font"  in kwargs else QFont("Fira Sans", 12)
        label = kwargs.get("label") if "label" in kwargs else ""
        width = kwargs.get("width") if "width" in kwargs else 80
        color = kwargs.get("color") if "color" in kwargs else Qt.GlobalColor.black
        brush = kwargs.get("brush") if "brush" in kwargs else Qt.BrushStyle.NoBrush
        align = kwargs.get("align") if "align" in kwargs else Qt.AlignmentFlag.AlignLeft

        # Set alignment:
        option = self.document().defaultTextOption()
        option.setAlignment(align)

        # Set edit flag:
        self.edit = edit
        self.flag = Qt.TextInteractionFlag.TextEditorInteraction if edit else Qt.TextInteractionFlag.NoTextInteraction

        # Customize attribute(s):
        try:
            self.setFont(font)
            self.setPlainText(label)
            self.setTextWidth(width)
            self.setDefaultTextColor(color)
            self.setTextInteractionFlags(self.flag)
            self.document().setDefaultTextOption(option)

        except TypeError as error:
            print(f"Label.__init__(): Invalid keyword-arguments")
            pass

    # Keyboard-event handler:
    def keyPressEvent(self, event):

        # When the <Return> key is pressed, clear focus to exit edit mode:
        if event.key() == Qt.Key.Key_Return:
            self.clearFocus()
            event.accept()
            return

        # Otherwise, handle event normally:
        super().keyPressEvent(event)

    def focusOutEvent(self, event):

        # Clear text-selection and emit signal:
        self.textCursor().clearSelection()
        self.sig_text_changed.emit(self.toPlainText())

        if not self.edit:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        # Super-class implementation:
        super().focusOutEvent(event)

    def paint(self, painter, option, widget):
        option.state = QStyle.StateFlag.State_None
        super().paint(painter, option, widget)