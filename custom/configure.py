"""
configure.py
"""
from PyQt6.QtCore import Qt
# PyQt6 Library:
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QGridLayout, QTextEdit, QDialogButtonBox, QComboBox, QFormLayout, QFrame, QLabel, QVBoxLayout, QStackedWidget,
    QCheckBox, QHBoxLayout, QLineEdit, QSizePolicy
)

import pyqtgraph
from .entity import *
from .evolution import EvolutionType
from .separator import Separator

# Class EntityConfigure:
class EntityConfigure(QWidget):
    """
    Configuration class for an entity with a name and a description.
    """
    def __init__(self, entity: Entity | None, parent: QWidget | None = None):
        super().__init__(parent)
        super().setStyleSheet("QLineEdit {"
                                "font: 14pt 'Didot';"
                                "width: 30px;"
                                "color: white;"
                                "background: darkgray;"
                                "}"
                                "QLabel {"
                                "font: 14pt 'Didot';"
                                "width: 60px;"
                                "}")

        val_label = QLabel("Value (f[t]):")
        sig_label = QLabel("Sigma (f[t]):")
        min_label = QLabel("Max (f[t]):")
        max_label = QLabel("Min (f[t]):")

        val_combo = (QComboBox(self))
        val_combo.addItems(["Constant", "Linear", "Quadratic", "Cubic", "Sigmoid"])
        val_combo.currentTextChanged.connect(self.change_stack)

        sig_combo = QComboBox(self)
        sig_combo.addItems(["Constant", "Linear", "Quadratic", "Cubic", "Sigmoid"])

        min_combo = QComboBox(self)
        min_combo.addItems(["Constant", "Linear", "Quadratic", "Cubic", "Sigmoid"])

        max_combo = QComboBox(self)
        max_combo.addItems(["Constant", "Linear", "Quadratic", "Cubic", "Sigmoid"])

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)

        graph_1 = pyqtgraph.PlotWidget()
        graph_2 = pyqtgraph.PlotWidget()
        graph_3 = pyqtgraph.PlotWidget()

        graph_1.setBackground("w")
        graph_2.setBackground("w")
        graph_3.setBackground("w")

        self._wstack = QStackedWidget(self)
        self._wstack.addWidget(self.create_graph(EvolutionType.CONSTANT))
        self._wstack.addWidget(self.create_graph(EvolutionType.LINEAR))
        self._wstack.addWidget(self.create_graph(EvolutionType.QUADRATIC))
        self._wstack.addWidget(self.create_graph(EvolutionType.CUBIC))
        self._wstack.addWidget(self.create_graph(EvolutionType.SIGMOID))

        self._layout.addWidget(val_label, 0, 0)
        self._layout.addWidget(val_combo, 0, 1)
        self._layout.addWidget(sig_label, 0, 2)
        self._layout.addWidget(sig_combo, 0, 3)
        self._layout.addWidget(min_label, 0, 4)
        self._layout.addWidget(min_combo, 0, 5)
        self._layout.addWidget(max_label, 0, 6)
        self._layout.addWidget(max_combo, 0, 7)
        self._layout.addWidget(QLabel("Value f[t]:"), 1, 0)
        self._layout.addWidget(QLineEdit(), 1, 1)
        self._layout.addWidget(QLabel("Sigma f[t]:"), 1, 2)
        self._layout.addWidget(QLineEdit(), 1, 3)
        self._layout.addWidget(QLabel("Max f[t]:"), 1, 4)
        self._layout.addWidget(QLineEdit(), 1, 5)
        self._layout.addWidget(QLabel("Min f[t]:"), 1, 6)
        self._layout.addWidget(QLineEdit(), 1, 7)
        self._layout.addWidget(self._wstack, 2, 0, 1, 8)

    @staticmethod
    def create_graph(curve: EvolutionType):
        """
        Create a widget that displays the coefficients of the given evolution type.
        :param curve:
        :return:
        """
        container = QFrame(None)
        container.setStyleSheet("QLineEdit {"
                                "font: 14pt 'Didot';"
                                "width: 30px;"
                                "color: white;"
                                "background: darkgray;"
                                "}"
                                "QLabel {"
                                "font: 14pt 'Didot';"
                                "width: 60px;"
                                "}")

        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        co = QLineEdit("c")
        lm = QLineEdit("m")
        li = QLineEdit("c")

        cd = QLineEdit("d")
        cc = QLineEdit("c")
        cb = QLineEdit("b")
        ca = QLineEdit("a")

        sa = QLineEdit("")
        s1 = QLineEdit("")
        sb = QLineEdit("")
        s2 = QLineEdit("")

        crow = 1
        """
        if  curve == EvolutionType.CONSTANT:
            layout.addWidget(QLabel("Y = "), 0, 0)
            layout.addWidget(co, crow, 1)

        elif curve == EvolutionType.LINEAR:
            layout.addWidget(QLabel("Y = "), 0, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(lm, crow, 1, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X + "), 0, 2, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(li, crow, 3, Qt.AlignmentFlag.AlignLeft)

        elif curve == EvolutionType.QUADRATIC:
            layout.addWidget(QLabel("Y = "), 0, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(ca, crow, 1, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X<sup>2</sup> + "), 0, 2, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(cb, crow, 3, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X + "), 0, 4, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(cc, crow, 5, Qt.AlignmentFlag.AlignLeft)

        elif curve == EvolutionType.CUBIC:
            layout.addWidget(QLabel("Y = "), 0, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(ca, crow, 1, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X<sup>3</sup> + "), 0, 2, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(cb, crow, 3, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X<sup>2</sup> + "), 0, 4, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(cc, crow, 5, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("X + "), 0, 6, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(cd, crow, 7, Qt.AlignmentFlag.AlignLeft)

        elif curve == EvolutionType.SIGMOID:
            layout.addWidget(QLabel("Y = "), 0, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(sa, crow, 1, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel(" / (1 + EXP(-X -"), 0, 2, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(s1, crow, 3, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel(")) + "), 0, 4, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(sb, crow, 5, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel(" / (1 + EXP(-X -"), 0, 6, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(s2, crow, 7, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(QLabel("))"), 0, 8, Qt.AlignmentFlag.AlignLeft)
        """

        graph = pyqtgraph.PlotWidget()
        graph.setBackground("w")

        layout.addWidget(graph, 0, 0, 1, 10, Qt.AlignmentFlag.AlignLeft)
        return container

    def change_stack(self, label):

        if label.lower() == "constant":
            self._wstack.setCurrentIndex(0)

        elif label.lower() == "linear":
            self._wstack.setCurrentIndex(1)

        elif label.lower() == "quadratic":
            self._wstack.setCurrentIndex(2)

        elif label.lower() == "cubic":
            self._wstack.setCurrentIndex(3)

        elif label.lower() == "sigmoid":
            self._wstack.setCurrentIndex(4)