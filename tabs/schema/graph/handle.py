import weakref, logging

from PyQt6.QtCore import QRectF, Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QTextCursor, QActionGroup, QAction, QCursor, QPixmap, QIcon, \
    QPainter
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject, QMenu, QGraphicsEllipseItem, QGraphicsTextItem, QLineEdit, \
    QWidgetAction, QLabel, QWidget, QHBoxLayout

from dataclasses    import dataclass


from core.category import CategoryAction
from core.label import Label
from core.resource import Resource, Category
from core.util import random_id
from tabs.schema.action import DisconnectHandleAction
from tabs.schema.graph.anchor import StreamType

class Handle(QGraphicsObject, Resource):

    # Signals:
    sig_item_clicked = pyqtSignal(QGraphicsObject)
    sig_item_updated = pyqtSignal(QGraphicsObject)
    sig_item_shifted = pyqtSignal(QGraphicsObject)
    sig_item_removed = pyqtSignal(QGraphicsObject)

    # Copy map:
    cmap = {}

    @dataclass
    class Attr:
        size = 5.0
        rect = QRectF(-size/2.0, -size/2.0, size, size)

    @dataclass
    class Style:
        def __init__(self):
            self.pen_border = QPen(Qt.GlobalColor.black, 1.0)
            self.background = QBrush(Qt.GlobalColor.green)
            self.bg_paired  = QBrush(QColor(0xff3a35))
            self.bg_active  = self.background

    # Initializer:
    def __init__(self, coords: QPointF, symbol: str, stream: StreamType, parent: QGraphicsObject | None):

        # Initialize base-class:
        super().__init__(parent)

        # Display the handle's symbol
        self._label  = Label(self,
                             edit=False,
                             label=symbol,
                             font=QFont("Nunito", 12),
                             align=Qt.AlignmentFlag.AlignRight if stream == StreamType.OUT else Qt.AlignmentFlag.AlignLeft)
        self._label.setPos(7.5 if stream == StreamType.INP else -self._label.textWidth() - 7.5, -13)
        self._label.sig_text_changed.connect(self.rename)

        # Attrib (Must be defined after `_label`):
        self._attr = self.Attr()
        self._styl = self.Style()
        self._huid = random_id(prefix='H')

        self.offset = coords.toPoint().x()
        self.stream = stream
        self.symbol = symbol
        self.label  = symbol

        # Connection status:
        self.connected = False
        self.conjugate = None
        self.connector = None
        self.isLabeled = True

        # Hover hint:
        self._hint = QGraphicsEllipseItem(QRectF(-1.0, -1.0, 2.0, 2.0), self)
        self._hint.setBrush(Qt.GlobalColor.black)
        self._hint.setPen(QPen())
        self._hint.hide()

        # Behaviour:
        self.setPos(coords)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Initialize menu:
        self._menu = None
        self._init_menu()

    def __hash__(self):     return hash(self.uid)

    def __eq__(self, other):
        return isinstance(other, Handle) and self._huid == other._huid

    # Context-menu initializer:
    def _init_menu(self):

        # Initialize menu:
        self._menu = QMenu()
        self._subm = self._menu.addMenu("Stream")

        # Main menu actions:
        edit_action = self._menu.addAction("Edit Label")
        edit_action.triggered.connect(self.edit_label)
        edit_action.setObjectName("Edit Label")

        unpair_action = self._menu.addAction("Unpair")
        unpair_action.triggered.connect(self.unpair)
        unpair_action.setObjectName("Unpair")

        delete_action = self._menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.sig_item_removed.emit(self))
        delete_action.setObjectName("Delete")

        # Sub-menu customization:
        prompt = QLineEdit()
        prompt.setPlaceholderText("Enter Category")
        prompt.returnPressed.connect(lambda: self.get_prompt(prompt))

        action = QWidgetAction(self._subm)
        action.setDefaultWidget(prompt)
        self._subm.addAction(action)
        self._subm.addSeparator()

    @property
    def uid(self):  return self._huid

    @property
    def background(self):
        return self._styl.background

    @background.setter
    def background(self, value):
        self._styl.background = value if isinstance(value, QBrush) else self.background

    # Make the handle's label temporarily editable:
    def edit_label(self):

        # Edit only if `isLabeled` flag is True:
        if not self.isLabeled:
            return

        # Make the label temporarily editable:
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._label.setFocus(Qt.FocusReason.OtherFocusReason)

        # Highlight the entire word:
        cursor = self._label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        self._label.setTextCursor(cursor)

    # Unpair this handle:
    def unpair(self):

        # Initiate unpairing through stack-manager:
        if self.connected:
            action = DisconnectHandleAction(self.scene(), self.connector())

    # Rename when the label is changed:
    def rename(self, label: str):
        self.label = label
        self._label.setPlainText(self.label)

    def boundingRect(self):
        return QRectF(-2.0 * self.Attr.size, -2.0 * self.Attr.size, 4.0 * self.Attr.size, 4.0 * self.Attr.size)

    def paint(self, painter, option, widget = ...):
        painter.setPen(self._styl.pen_border)
        painter.setBrush(self._styl.bg_active)
        painter.drawEllipse(self._attr.rect)

    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.sig_item_shifted.emit(self)

        return value

    def contextMenuEvent(self, event):

        unpair = self._menu.findChild(QAction, name="Unpair")
        unpair.setEnabled(self.connected)

        edit = self._menu.findChild(QAction, name="Edit Label")
        edit.setEnabled(self.isLabeled)

        # Create an actions-list:
        menu_actions = list()

        # Add dynamic categories:
        for _category in Category.Set:

            # Skip empty categories:
            if not bool(_category.cname):   continue

            # Create category-actions:
            action = CategoryAction(_category, _category.cname == self.cname)
            action.triggered.connect(self.get_action)

            menu_actions.append(action)
            self._subm.addAction(action)

        self._menu.popup(QCursor.pos())
        self._menu.exec()

        # Once the menu has been closed, remove all actions:
        for action in menu_actions:
            self._subm.removeAction(action)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self._huid)

        self._hint.show()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):

        self._hint.hide()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            if not self.connected:
                self.sig_item_clicked.emit(self)

            elif self.isLabeled:
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.setPos(self.offset, self.pos().y())
        super().mouseReleaseEvent(event)

    def lock(self, conjugate, connector):

        # Store references:
        self.connected = True
        self.conjugate = weakref.ref(conjugate)
        self.connector = weakref.ref(connector)

        # Change background color to red:
        self._styl.bg_active = self._styl.bg_paired

    def free(self):

        # Store references:
        self.connected = False
        self.conjugate = None
        self.connector = None

        # Change background color to green:
        self._styl.bg_active = self._styl.background

        # Make item immovable again:
        logging.info(f"Freeing {self.uid}")
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def get_action(self):

        # Type-check:
        _action = self.sender()
        if not isinstance(_action, CategoryAction):
            return

        # Get category by name:
        _cat_name = _action.action_label()
        if _cat_name is None:
            return

        # Set category:
        _category = Category.find_category_by_label(_cat_name)
        self.cname = _category.cname
        self.color = _category.color

        # Emit updated signal:
        self.sig_item_updated.emit(self)

    def get_prompt(self, _prompt: QLineEdit):

        # User-entry:
        _new_label = _prompt.text()
        _prompt.clear()

        # Abort if prompt is empty:
        if not bool(_new_label):
            return

        # Assign category:
        _category = Category.find_category_by_label(_new_label)
        self.cname = _category.cname
        self.color = _category.color
        self._menu.close()

        # Emit signal:
        self.sig_item_updated.emit(self)
