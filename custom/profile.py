from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


class Profile(QGraphicsTextItem):

    # Signals:
    sig_text_changed = pyqtSignal(str, name="Text Changed")
    sig_tabs_pressed = pyqtSignal(name="Tab Pressed")

    # Attributes:
    class Attr:
        width = 120
        upper = False
        align = Qt.AlignmentFlag.AlignCenter
        font  = QFont("Menlo", 9)

    # Style:
    class Style:
        pen_default = Qt.PenStyle.NoPen
        pen_focused = QPen(QColor(0x0), 1.0)

        background  = QBrush(QColor(0xefefef), Qt.BrushStyle.SolidPattern)
        foreground  = pen_focused.color()

    # Constructor:
    def __init__(self, text: str, editable: bool, parent_item: QGraphicsItem):

        # Initialize base-class:
        super().__init__(parent_item)

        # Attrib:
        self._attr = self.Attr()
        self._styl = self.Style()
        self._edit = editable

        # Customize appearance and attributes:
        if editable:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

        # Visual attribute(s):
        self.setDefaultTextColor(self._styl.foreground)
        self.setTextWidth(self._attr.width)
        self.setFont(self._attr.font)

        # Item behaviour:
        self.setAcceptHoverEvents(True)

        # Set text:
        self.setPlainText(text)

    # Event-handler for paint events:
    def paint(self, painter, option, widget):

        # Set pen and brush:
        painter.setPen(self._styl.pen_focused  if (self.hasFocus() and self._edit) else Qt.PenStyle.NoPen)
        painter.setBrush(self._styl.background if (self.hasFocus() and self._edit) else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0, 2, self.textWidth() + 4, 20), 2, 2)

        # Remove the ugly dotted border when the item is selected:
        option.state = QStyle.StateFlag.State_None

        # Call base-class implementation to finish event-handling:
        super().paint(painter, option, widget)

    # Set alignment:
    def set_alignment(self, alignment):
        option = self.document().defaultTextOption()
        option.setAlignment(alignment)
        self.document().setDefaultTextOption(option)

    # Toggle upper case characters only (useful for enforcing capitalization in title-items):
    def set_upper_case_only(self, is_upper_case: bool):
        self._attr.upper = is_upper_case
        if is_upper_case:
            self.setPlainText(self.toPlainText().upper())

    # Upon focus loss, notify text-change signal:
    def focusOutEvent(self, event):
        self.textCursor().clearSelection()
        self.sig_text_changed.emit(self.toPlainText())
        super().focusOutEvent(event)

    # On <Key_Return> press, clear focus and accept edited text:
    def keyPressEvent(self, event):

        # When the <Return> key is pressed, clear focus to exit edit mode:
        if event.key() == Qt.Key.Key_Return:
            self.clearFocus()
            event.accept()
            return

        # Otherwise, handle event normally:
        super().keyPressEvent(event)

        # If required, enforce uppercase characters:
        if  self._attr.upper:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            self.setPlainText(self.toPlainText().upper())
            self.setTextCursor(cursor)

    # Event-handler for hover-enter:
    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setOpacity(0.6 if self._edit else 1.0)

    # Event-handler for hover-leave:
    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.setOpacity(1.0)


