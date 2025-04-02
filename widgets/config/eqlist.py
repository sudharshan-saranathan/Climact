from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

class Equation(QListWidgetItem):

    def __init__(self, parent: QListWidget):

        # Initialize base-class:
        super().__init__(parent)

        # Upload icon:
        self.setIcon(QIcon("rss/icons/trash.png"))

class Eqlist(QListWidget):

    # Signals:
    sig_notify_config = pyqtSignal(str)

    # Constructor:
    def __init__(self, parent = None):

        # Initialize base-class:
        super().__init__(parent)

    # Store equations as list-items:
    def insert_equations(self, equations_list):

        for equation in equations_list:
            if not self.findItems(equation, Qt.MatchFlag.MatchExactly):
                equation_item = Equation(self)
                equation_item.setText(equation)
                self.addItem(equation_item)

            else:
                print(f"Equation already exists, ignoring duplicate")

    # Delete equations with given symbols:
    def delete_symbols(self, symbol: str):
        items = self.findItems(symbol, Qt.MatchFlag.MatchContains)
        for item in items:
            self.takeItem(self.row(item))

    # Replace symbols in equations:
    def replace_symbols(self, symbol: str, replacement: str):
        items = self.findItems(symbol, Qt.MatchFlag.MatchContains)
        for item in items:
            equation = item.text()
            equation = equation.replace(symbol, replacement)
            item.setText(equation)

        self.update()

    # Retrieve stored equations:
    def fetch_equations(self):

        equations = list()
        for index in range(self.count()):
            equations.append(self.item(index).text())

        return equations

    def mousePressEvent(self, event):

        item = self.itemAt(event.pos())
        if item:
            rect = self.visualItemRect(item)
            rect.setWidth(30)

            if rect.contains(event.pos()):
                self.takeItem(self.row(item))

        super().mousePressEvent(event)