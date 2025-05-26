import re
import weakref

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtWidgets import QListWidget, QWidget, QMenu, QTextEdit, QDialog, QVBoxLayout, QListWidgetItem, QAbstractItemView, QMessageBox

from custom import EntityClass
from tabs.schema import Canvas

# Class Equation-View:
class EqnView(QListWidget):

    # Initializer:
    def __init__(self,
                 _canvas: Canvas,   # Required for validating symbols
                 _parent: QWidget   # Parent widget
                 ):

        # Initialize super-class:
        super().__init__(_parent)

        # Reference to the _node being updated, initialize with `None`:
        self._node = None
        self._symb = []

        # Customize behavior:
        self.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)

        # Initialize menus:
        self._menu = None
        self._init_menu()

    @property
    def node(self): return self._node()

    @node.setter
    def node(self, _node):

        # Store weak-reference:
        self._node = weakref.ref(_node)

        # Fetch equations:
        self.fetch()

    @property
    def symbols(self):  return self._symb

    @symbols.setter
    def symbols(self, value):

        # Validate arguments:
        if not isinstance(value, list): raise TypeError("Expected argument of type `list[str]`")

        # Assign data:
        self._symb = value

    def _init_menu(self):

        # Create a context menu:
        self._menu = QMenu(self)

        # Initialize actions:
        _insert = self._menu.addAction("Insert Equation(s)", self.get_equations_from_user)
        _delete = self._menu.addAction("Delete Equation(s)", self.delete_equations)

    def contextMenuEvent(self, event):
        # Open menu at cursor position:
        self._menu.exec(event.globalPos())
        event.accept()

    def get_equations_from_user(self):

        # Abort if no _node has been set:
        if self._node() is None:
            return

        # Otherwise, open a text-editor:
        dialog = QDialog(None)
        dialog.setModal(False)
        dialog.setFixedSize(600, 400)

        # Create a text editor:
        editor = QTextEdit()
        editor.setPlaceholderText("1. Enter equations in residual form.\n"
                                  "2. Enter one equation per line.\n"
                                  "3. Press <Ctrl> + <Enter> to insert equations.\n")

        # Install layout:
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(editor)

        # Add shortcuts:
        ctrl_return = QShortcut(QKeySequence("Ctrl+Return"), editor)
        ctrl_return.activated.connect(dialog.accept)

        # Execute dialog and insert equations:
        if  dialog.exec() == QDialog.DialogCode.Accepted:
            equations = editor.toPlainText().split('\n')
            self.parse(equations)

    def delete_equations(self):

        # Get selected items:
        equations = self.selectedItems()

        # Delete selected items:
        for equation in equations:
            # Verify that the equation is in the node's equations:
            if equation.text() not in self._node()[EntityClass.EQN]:
                continue

            self._node()[EntityClass.EQN].remove(equation.text())
            self.takeItem(self.row(equation))

    def parse(self, equations):

        # Abort if no _node has been set:
        if self._node() is None:
            return

        # Validate equations:
        for equation in equations:
            equation = re.sub(r'([^\w\s.])', r' \1 ', equation)     # Add space around symbols
            equation = re.sub(r'\s+', ' ', equation).strip()        # Remove multiple spaces

            # Equation must have exactly 1 '=', it must not start or end with a '=':
            if (
                equation.count('=') == 1    and
                not equation.endswith('=')  and
                not equation.startswith('=')
            ):
                sym_eqn = set(re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', equation))  # Equation symbols
                sym_tot = self._symb

                print(sym_eqn)
                print(sym_tot)

                # Insert equation:
                self.insert_item(equation)

                """
                # Validate symbols:
                if  sym_eqns.issubset(sym_node):    self.insert_item(equation)

                else:
                    # Display error message:
                    warning = Message(QtMsgType.QtCriticalMsg,
                                     f"Unrecognized variable(s):\n{str(', ').join(sym_eqns - sym_node)}",
                                     QMessageBox.StandardButton.Ok)

                    warning.exec()

            else:
                # Display error message:
                error = Message(QtMsgType.QtCriticalMsg,
                               f"Equation must have exactly one '='",
                               QMessageBox.StandardButton.Ok)

                error.exec()
            """

    def insert_item(self, equation):

        item = QListWidgetItem(equation)
        item.setIcon(QIcon("rss/icons/trash.png"))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        self.addItem(item)
        self._node()[EntityClass.EQN].append(equation)

    # Fetch and display _node's equations
    def fetch(self):

        # Clear all list items:
        super().clear()             # Use super().clear(), not self.clear() to avoid resetting node-reference

        # Confirm reference validity:
        if self._node() is None:
            return

        # Fetch equations and display them:
        equations = self._node()[EntityClass.EQN]
        for equation in equations:

            # Create a list-item for each equation:
            item = QListWidgetItem(equation)
            item.setIcon(QIcon("rss/icons/trash.png"))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.addItem(item)

    # Clear list-items:
    def clear(self):
        super().clear()
        self._node = None
        self.setDisabled(True)


