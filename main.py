# System-imports
import sys

# User-defined:
from core.core_gui   import Gui
from PyQt6.QtGui     import QFont
from PyQt6.QtCore    import QFile
from PyQt6.QtWidgets import QApplication


def style():

    file = QFile("rss/style/macos.qss")
    file.open(QFile.OpenModeFlag.ReadOnly)
    
    qss  = file.readAll().data().decode("utf-8")
    return qss

def main():

    qss = style()
    app = QApplication(sys.argv)

    app.setFont(QFont("Menlo", 12))
    app.setStyleSheet(qss)

    gui = Gui()
    sys.exit(app.exec())

main()