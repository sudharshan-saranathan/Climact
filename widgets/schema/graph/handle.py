from core.core_qss          import QSS
from custom.profile         import *
from widgets.schema.graph.anchor import *

class Category:

    # Global list:
    List = list()

    # Constructor:
    def __init__(self, _category: str = "Default", _color: QColor = QColor(Qt.GlobalColor.darkGray)):
        self._category = _category
        self._color    = _color

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, __value: str):
        self._category = __value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, __value: QColor):
        self._color = __value if isinstance(__value, QColor) else self._color
        if isinstance(self, Handle):
            self._label.setDefaultTextColor(self._color)
            if self.connected and self._strm == Stream.OUT:
                self.conjugate.category = self._category
                self.conjugate.color    = self._color
                self.connector.color    = self._color

    @staticmethod
    def find_category_by_label(category     : str,
                               create_new   : bool = True,
                               ignore_case  : bool = True
                               ):

        for _category in Category.List:

            label =  category
            match = _category.category
            if ignore_case:
                label = label.lower()
                match = match.lower()

            if label == match:
                return _category

        if create_new:
            __new_category = Category(category, QSS.random_hex())
            Category.List.append(__new_category)
            return __new_category

        return None

class Resource(Category):

    # Initialization:
    def __init__(self):

        # Initialize base-class:
        super().__init__()

        # Dictionary of the resource's properties:
        self.__property = {
            "ID"        : None,
            "Symbol"    : None,
            "Label"     : None,
            "Info"      : None,
            "Unit"      : None,
            "Value"     : None,
            "Lower"     : None,
            "Upper"     : None,
            "Delta"     : None,
            "Sigma"     : None,
            "Result"    : None,
            "Category"  : "Default",
            "Color"     : QColor(Qt.GlobalColor.gray)
        }

    @property
    def id(self):
        return self.__property["ID"]

    @id.setter
    def id(self, __value):
        self.__property["ID"] = __value

    @property
    def symbol(self):
        return self.__property["Symbol"]

    @symbol.setter
    def symbol(self, __value):
        self.__property["Symbol"] = __value

    @property
    def label(self):
        return self.__property["Label"]

    @label.setter
    def label(self, __value):
        self.__property["Label"] = __value
        if isinstance(self, Handle):
            self._label.setPlainText(__value)
            if self.connected and self._strm == Stream.OUT:
                self.conjugate.label = __value

    @property
    def info(self):
        return self.__property["Info"]

    @info.setter
    def info(self, __value):
        self.__property["Info"] = __value

    @property
    def unit(self):
        return self.__property["Unit"]

    @unit.setter
    def unit(self, __value):
        self.__property["Unit"] = __value

    @property
    def value(self):
        return self.__property["Value"]

    @value.setter
    def value(self, __value: float):
        self.__property["Value"] = __value if isinstance(__value, float) else self.value

    @property
    def lower(self):
        return self.__property["Lower"]

    @lower.setter
    def lower(self, __value: float):
        self.__property["Lower"] = __value if isinstance(__value, float) else self.lower

    @property
    def upper(self):
        return self.__property["Upper"]

    @upper.setter
    def upper(self, __value: float):
        self.__property["Upper"] = __value if isinstance(__value, float) else self.upper

    @property
    def delta(self):
        return self.__property["Delta"]

    @delta.setter
    def delta(self, __value: float):
        self.__property["Delta"] = __value if isinstance(__value, float) else self.delta

    @property
    def sigma(self):
        return self.__property["Sigma"]

    @sigma.setter
    def sigma(self, __value: float):
        self.__property["Sigma"] = __value if isinstance(__value, float) else self.sigma

    @property
    def result(self):
        return self.__property["Result"]

    @result.setter
    def result(self, __value: float):
        self.__property["Result"] = __value if isinstance(__value, float) else self.result

    @property
    def properties(self):
        return self.__property.keys()

    # This method creates a new property for handle:
    def create_property(self, key: str, value: str | float):

        if not bool(key):
            return

        # Create a new key-value pair:
        self.__property[key] = value

    def duplicate(self):
        new_resource = Resource()
        new_resource.__property = self.__property.copy()

        return new_resource

class Handle(QGraphicsObject, Resource):

    # Hash-map (shared attribute):
    cmap = {}

    # Signals:
    sig_item_clicked = pyqtSignal()
    sig_item_deleted = pyqtSignal()
    sig_item_shifted = pyqtSignal()
    sig_item_updated = pyqtSignal()

    # Attrib:
    class Attr:
        rect   = QRectF(-20, -20, 40, 40)
        circ   = QRectF(-2.5, -2.5, 5.0, 5.0)
        offset = 0.0

    # Style:
    class Style:
        def __init__(self):
            self.pen_default = QPen(Qt.GlobalColor.black)
            self.pen_clicked = QPen(Qt.GlobalColor.green)
            self.background  = Qt.GlobalColor.green

    def __init__(self, symbol: str, stream: Stream, parent: QGraphicsItem):

        # Initialize base-classes:
        super().__init__(parent)
        Resource.__init__(self)   # Explicitly initialize Resource
        Category.__init__(self)   # Explicitly initialize Category

        # Generate unique ID:
        self.id = QSS.random_id(length=4, prefix="H#")

        # Attrib:
        self._attr = self.Attr()
        self._styl = self.Style()
        self._strm = stream

        # Metadata:
        self.connected = False
        self.conjugate = None
        self.connector = None

        # Initialize label:
        self._label = Profile(symbol, False, self)
        self._label.set_alignment(Qt.AlignmentFlag.AlignRight if stream == Stream.OUT else Qt.AlignmentFlag.AlignLeft)
        self._label.setPos(7.5 if stream == Stream.INP else -self._label.textWidth() - 7.5, -12)

        self._label.sig_text_changed.connect(self.auto_categorize)
        self._label.sig_text_changed.connect(self.sig_item_updated.emit)
        self._label.sig_text_changed.connect(lambda: self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction))

        # Initialize hint:
        self._hint = QGraphicsEllipseItem(QRectF(-1.5, -1.5, 3, 3), self)
        self._hint.setPen(QPen(Qt.PenStyle.NoPen))
        self._hint.setBrush(Qt.GlobalColor.black)
        self._hint.hide()

        # Resource-attrib:
        self.label  = symbol
        self.symbol = symbol
        self.color  = Qt.GlobalColor.gray

        # Initialize context-menu:
        self.__menu__()

        # Behaviour:
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

    def __menu__(self):

        # Create menu:
        self._menu = QMenu()
        self._subm = self._menu.addMenu("Configure")
        self._subm.addSeparator()

        # Add actions:
        edit   = self._menu.addAction("Edit Label")
        unpair = self._menu.addAction("Unpair")
        delete = self._menu.addAction("Delete")

        # Add a line-edit to the menu:
        prompt = QLineEdit()
        prompt.setPlaceholderText("Enter Category")

        action = QWidgetAction(self._subm)
        action.setDefaultWidget(prompt)
        self._subm.addAction(action)
        self._subm.addSeparator()

        unpair.setObjectName("Unpair")
        delete.setObjectName("Delete")

        edit  .triggered.connect(self.edit)
        unpair.triggered.connect(self.unpair)
        delete.triggered.connect(self.delete)
        delete.triggered.connect(self.sig_item_deleted.emit)

    @property
    def snap(self):
        return self._attr.offset

    @snap.setter
    def snap(self, __value: float):
        self._attr.offset = __value

    def paint(self, painter, option, widget = ...):
        painter.setPen(self._styl.pen_default)
        painter.setBrush(self._styl.background)
        painter.drawEllipse(self._attr.circ)

    def stream(self):
        return self._strm

    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            self.sig_item_shifted.emit()

        return value

    def boundingRect(self):
        return self._attr.rect

    def edit(self):

        text_cursor = self._label.textCursor()
        text_cursor.select(QTextCursor.SelectionType.Document)

        self._label.setTextCursor(text_cursor)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self._label.setFocus(Qt.FocusReason.OtherFocusReason)

    def unpair(self):
        if self.connected:
            self.connector.delete()

    def delete(self):

        if self.connected:
            self.connector.delete()

        self.deleteLater()

    def get_action(self):

        # Validate signal-emitter:
        _action = self.sender()
        if not isinstance(_action, QAction):
            return

        # Get the category by name:
        _category = Category.find_category_by_label(_action.text())
        self.category = _category.category
        self.color    = _category.color

        # Emit updated signal:
        self.sig_item_updated.emit()

    # Auto-categorizer parses the handle's label and selects a category:
    def auto_categorize(self):

        __hlabel = self._label.toPlainText()
        __tokens = __hlabel.lower().split(' ')

        __name_set = {cat.category.lower() for cat in Category.List}
        __labl_set = {word for word in __tokens}
        __intersection = __name_set & __labl_set

        self.label = __hlabel
        if len(__intersection) == 1:
            self.category = __intersection.pop()
            self.color    = Category.find_category_by_label(self.category).color

    def contextMenuEvent(self, event):

        unpair = self._menu.findChild(QAction, name="Unpair")
        unpair.setEnabled(self.connected)

        # Create an actions-list:
        actions = list()

        # Add dynamic categories:
        for _category in Category.List:

            action = self._subm.addAction(_category.category)
            action.triggered.connect(self.get_action)
            action.setCheckable(True)
            actions.append(action)

            if action.text() == self.category:
                action.setChecked(True)

        self._menu.popup(QCursor.pos())
        self._menu.exec()

        # Once the menu has been closed, remove all actions:
        for action in actions:
            self._subm.removeAction(action)

    def hoverEnterEvent(self, event):

        super().hoverEnterEvent(event)
        self._hint.show()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self.id)

    def hoverLeaveEvent(self, event):

        super().hoverLeaveEvent(event)
        self._hint.hide()

        self.unsetCursor()
        self.setToolTip("")

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            if not self.connected:
                self.sig_item_clicked.emit()

            else:
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):

        self.setX(self.snap)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

        super().mouseReleaseEvent(event)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        print("Mouse double clicked")

        self._label.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mouseDoubleClickEvent(event)