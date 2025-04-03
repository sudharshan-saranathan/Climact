from dataclasses    import dataclass
from pathlib        import Path

from PyQt6.QtWidgets    import *
from PyQt6.QtCore       import *
from PyQt6.QtGui        import *

import os

class FileSystem(QTreeView):

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Initialize model:
        path = os.getcwd() + "/library/systems"
        self.__model = QFileSystemModel(self)
        self.__model.setRootPath(path)

        print(os.getcwd())

        # Set model:
        self.setModel(self.__model)
        self.setRootIndex(self.__model.index(path))

class Library(QScrollArea):

    # Signals:
    sig_template_selected = pyqtSignal(QToolButton, name="Library.sig_template_selected")

    # Dataclass:
    @dataclass(slots=True)
    class Attr:
        gridx = 3

    # Initializer
    def __init__(self, section: str, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Select style:
        self.setFixedHeight(250)
        self.setStyleSheet( "background: transparent;")

        # Attrib:
        self.__attr  = self.Attr()
        self.__count = 0

        # Main Widgets:
        self.__section = section

        # Container:
        self.__container = QWidget()

        # Scrollable:
        self.setWidgetResizable(True)
        self.setWidget(self.__container)

        # Grid Layout:
        self.__layout = QGridLayout(self.__container)
        self.__layout.setContentsMargins(2, 8, 2, 4)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def insert_icon(self, icon: str | QIcon, label: str):

        __button   = QToolButton()
        __button.setText(label)
        __button.setIcon(QIcon(icon))
        __button.setObjectName(self.__section)
        __button.setIconSize(QSize(48, 48))
        __button.setStyleSheet("QToolButton:hover {background: #ababab;}")
        __button.pressed.connect(lambda: self.sig_template_selected.emit(__button))

        __label = QLabel(label)
        __label.setWordWrap(True)
        __label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        __label.setFixedWidth(120)
        __label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        __label.setStyleSheet("background: transparent;")

        i, j = 2 * int(self.__count / self.Attr.gridx) + 2, int(self.__count % self.Attr.gridx)
        self.__layout.addWidget(__button, i    , j, Qt.AlignmentFlag.AlignCenter)
        self.__layout.addWidget(__label , i + 1, j, Qt.AlignmentFlag.AlignCenter)
        self.__count = self.__count + 1

    def clear_grid(self):

        while self.__layout.count():
            item = self.__layout.takeAt(0)
            item.widget().deleteLater()

        self.__count = 0

class ComponentLibrary(QFrame):

    # Signals:
    sig_close = pyqtSignal(name="ComponentLibrary.sig_close")

    # Initializer:
    def __init__(self, parent: QWidget | None):

        # Initialize base-class:
        super().__init__(parent)

        # Set style:
        self.setObjectName("Library")
        self.setStyleSheet("#Library {"
                           "border          : 2px solid black;"
                           "margin          : 0px;"
                           "background      : #597788;"
                           "border-radius   : 12px;"
                           "}"
                           "QLabel {"
                           "border      : None;"
                           "color       : white;"
                           "background  : transparent;"
                           "}")

        # Main widgets:
        self.__components = QWidget()
        self.__systems    = QWidget()
        self.__close      = QToolButton(self)
        self.__refresh    = QToolButton(self)

        self.__close.setStyleSheet("margin: 0px; padding: 0px;")
        self.__close.setIcon(QIcon("rss/icons/close.png"))
        self.__close.setIconSize(QSize(24, 24))
        self.__close.pressed.connect(self.sig_close.emit)

        self.__refresh.setStyleSheet("margin: 0px; padding: 0px;")
        self.__refresh.setIcon(QIcon("rss/icons/refresh.png"))
        self.__refresh.setIconSize(QSize(24, 24))
        self.__refresh.pressed.connect(self.index_library)

        self.__hline_top = QFrame(self)
        self.__hline_mid = QFrame(self)
        self.__hline_top.setFrameShape(QFrame.Shape.HLine)
        self.__hline_mid.setFrameShape(QFrame.Shape.HLine)
        self.__hline_top.setFixedHeight(1)
        self.__hline_mid.setFixedHeight(1)
        self.__hline_top.setStyleSheet("background: lightgray;")
        self.__hline_mid.setStyleSheet("background: lightgray;")

        self.__com_library = Library("COMPONENTS", self)
        self.__sys_library = FileSystem(self)
        # self.__sys_library = Library("SYSTEMS"   , self)

        self.index_library()

        # Layout:
        __layout = QGridLayout(self)
        __layout.setContentsMargins(4, 8, 4, 8)
        __layout.setSpacing(2)

        __layout.addWidget(QLabel("COMPONENTS") , 0, 0)
        __layout.addWidget(self.__close         , 0, 2)
        __layout.addWidget(self.__refresh       , 0, 1)
        __layout.addWidget(self.__hline_top     , 1, 0, 1, 3)
        __layout.addWidget(self.__com_library   , 2, 0, 1, 3)
        __layout.addWidget(QLabel("SYSTEMS")    , 3, 0)
        __layout.addWidget(self.__hline_mid     , 4, 0, 1, 3)
        __layout.addWidget(self.__sys_library   , 5, 0, 1, 3)

        # Show widget:
        self.hide()

    @property
    def library(self):
        return {"Components": self.__com_library, "Systems": self.__sys_library}

    def index_library(self):

        self.__com_library.clear_grid()
        # self.__sys_library.clear_grid()

        __com_files = {file.name : file for file in Path("library/components/").glob("*.json")}
        __sys_files = {file.name : file for file in Path("library/systems/").glob("*.json")}

        for file in __com_files:
            self.__com_library.insert_icon("rss/icons/node.png", file.split('.')[0])


