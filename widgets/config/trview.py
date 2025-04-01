# TODO: Improve performance by updating instead of refreshing the whole tree when scene items are modified
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QTreeWidget, QWidget, QHeaderView, QGridLayout, QTreeWidgetItem, QLineEdit, \
    QPushButton

from widgets.schema import graph

class Trview(QTreeWidget):

    # Signals:
    sig_notify_config = pyqtSignal(str)

    # Constructor:
    def __init__(self, canvas, parent: QWidget = None):

        # Initialize base-class:
        super().__init__(parent)

        # Store canvas
        self._canvas = canvas
        self._canvas.sig_canvas_updated.connect(self.refresh, Qt.ConnectionType.DirectConnection)

        self.setColumnCount(4)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self.setColumnWidth(1, 60)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 40)

        self.setHeaderLabels(["ITEM", "STREAM", "PAIR", "EQS"])
        self.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(400)

        _searchbar = QLineEdit("")
        _searchbar.setFixedHeight(24)
        _searchbar.setMinimumWidth(330)
        _searchbar.setTextMargins(24, 2, 2, 2)
        _searchbar.setStyleSheet("border-radius: 6px; background: white;")
        _searchbar.setPlaceholderText("Type to search")
        _searchbar.textChanged.connect(self.search)

        _layout = QGridLayout(self)
        _layout.setContentsMargins(2, 2, 2, 2)
        _layout.setSpacing(4)

        _search_icon = QPushButton(QIcon("rss/icons/search.svg"), None, None)
        _expand_icon = QPushButton(QIcon("rss/icons/expand-all.svg"), None, None)
        _shrink_icon = QPushButton(QIcon("rss/icons/shrink-all.svg"), None, None)

        _search_icon.setFixedHeight(_searchbar.height())
        _expand_icon.setFixedHeight(_searchbar.height())
        _shrink_icon.setFixedHeight(_searchbar.height())

        _search_icon.setStyleSheet("background:transparent;")
        _search_icon.setEnabled(False)
        _expand_icon.pressed.connect(self.expandAll)
        _shrink_icon.pressed.connect(self.collapseAll)

        _layout.setRowStretch(0, 40)
        _layout.addWidget(_searchbar, 1, 0, Qt.AlignmentFlag.AlignLeft)
        _layout.addWidget(_search_icon, 1, 0, Qt.AlignmentFlag.AlignLeft)
        _layout.addWidget(_expand_icon, 1, 1, Qt.AlignmentFlag.AlignCenter)
        _layout.addWidget(_shrink_icon, 1, 2, Qt.AlignmentFlag.AlignCenter)

    def refresh(self):

        self.clear()
        self.update()

        for node in self._canvas.nodes:

            node_item = QTreeWidgetItem()
            node_item.setIcon(0, QIcon("rss/icons/checked.png"))
            node_item.setText(0, f"{node.nuid()}: {node.name()}")
            node_item.setText(1, f"{node.group}")

            for handle in node[graph.Stream.INP] + node[graph.Stream.OUT]:

                handle_item = QTreeWidgetItem(node_item, 0)
                handle_item.setIcon(0, QIcon("rss/icons/variable.png"))

                handle_item.setFlags(handle_item.flags() | Qt.ItemFlag.ItemNeverHasChildren)
                handle_item.setFlags(handle_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

                handle_item.setText(0, f"{handle.id}: {handle.label}")
                handle_item.setText(1, "INP" if handle.stream() == graph.Stream.INP else "OUT")
                handle_item.setText(2, handle.conjugate.id if handle.conjugate else "None")
                handle_item.setCheckState(3, Qt.CheckState.Unchecked)

                handle_item.setTextAlignment(1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                handle_item.setTextAlignment(2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                handle_item.setTextAlignment(3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            for parameter in node[graph.Stream.PAR]:

                par_item = QTreeWidgetItem(node_item, 0)
                par_item.setIcon(0, QIcon("rss/icons/parameter.png"))

                par_item.setFlags(par_item.flags() | Qt.ItemFlag.ItemNeverHasChildren)
                par_item.setFlags(par_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

                par_item.setText(0, f"{parameter.symbol}: {parameter.label}")
                par_item.setText(1, "PAR")
                par_item.setText(2, "None")
                par_item.setCheckState(3, Qt.CheckState.Unchecked)

                par_item.setTextAlignment(1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                par_item.setTextAlignment(2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            self.addTopLevelItem(node_item)
            self.collapseAll()

        print(f"INFO: Database update triggered, tree-items have been updated")

        # Automatically select the first item:
        if self.topLevelItemCount():
            self.topLevelItem(0).setSelected(True)
            self.setFocus(Qt.FocusReason.NoFocusReason)

    @pyqtSlot(str)
    def search(self, string):

        if len(string) < 2:
            return

        self.collapseAll()
        for index in range(self.topLevelItemCount()):

            node = self.topLevelItem(index)
            if string.upper() in node.text(0):
                node.setSelected(True)
                self.expandItem(node)

            else:
                node.setSelected(False)

            for j in range(node.childCount()):
                if string.lower() in node.child(j).text(0).lower():
                    self.expandItem(node)
                    node.child(j).setSelected(True)

                else:
                    node.child(j).setSelected(False)

    def update_icon(self, node: graph.Node, is_modified: bool):

        # Abort if node is not a node custom:
        if not isinstance(node, graph.Node):
            return

        item = self.findItems(node.nuid(), Qt.MatchFlag.MatchContains)[0]
        item.takeChildren()

        for handle in node[graph.Stream.INP] + node[graph.Stream.OUT]:

            handle_item = QTreeWidgetItem(item, 0)
            handle_item.setIcon(0, QIcon("rss/icons/variable.png"))

            handle_item.setFlags(handle_item.flags() | Qt.ItemFlag.ItemNeverHasChildren)
            handle_item.setFlags(handle_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

            handle_item.setText(0, f"{handle.id}: {handle.label}")
            handle_item.setText(1, "INP" if handle.stream() == graph.Stream.INP else "OUT")
            handle_item.setText(2, handle.conjugate.id if handle.conjugate else "None")
            handle_item.setCheckState(3, Qt.CheckState.Unchecked)

            handle_item.setTextAlignment(1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            handle_item.setTextAlignment(2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            handle_item.setTextAlignment(3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        for parameter in node[graph.Stream.PAR]:

            par_item = QTreeWidgetItem(item, 0)
            par_item.setIcon(0, QIcon("rss/icons/parameter.png"))

            par_item.setFlags(par_item.flags() | Qt.ItemFlag.ItemNeverHasChildren)
            par_item.setFlags(par_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)

            par_item.setText(0, f"{parameter.symbol}: {parameter.label}")
            par_item.setText(1, "PAR")
            par_item.setText(2, "None")
            par_item.setCheckState(3, Qt.CheckState.Unchecked)

            par_item.setTextAlignment(1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            par_item.setTextAlignment(2, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Change indicator:
        icon = QIcon("rss/icons/exclamation.png") if is_modified else QIcon("rss/icons/checked.png")
        item.setIcon(0, icon)
