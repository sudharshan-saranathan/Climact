"""
config.py
"""

import pyqtgraph
from PyQt6.QtCore import Qt

# PyQt6 library:
from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QVBoxLayout,
    QLabel,
    QStackedWidget
)

#
class Selector(QWidget):
    """
    Configuration class for database settings.
    """
    # Class constructor:
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        attribute = QComboBox()
        attribute.addItems(["Value", "Minimum", "Maximum"])

        curvetype = QComboBox()
        curvetype.addItems(["Constant", "Linear", "Quadratic", "Cubic", "Sigmoid"])

        self._wstack = QStackedWidget(self)
        self._wstack.setObjectName("Graph Stack")

        layout = QFormLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # layout.addRow("Attribute:" , attribute)
        # layout.addRow("Curve Type:", curvetype)
        layout.addRow("Graph:", self._wstack)
        self.setLayout(layout)

    def init_graph(self):
        """
        Add a graph to the stacked widget.
        :param x: X-axis data.
        :param y: Y-axis data.
        """

        charts = pyqtgraph.PlotWidget(self)
        charts.setBackground('w')
        charts.setLabel('left', "Value", units='units')
        charts.setLabel('bottom', "Time", units='h')
        charts.addLegend(offset=(0, 0), labelTextFormat='{value:.2f}')
        charts.showGrid(x=True, y=True, alpha=0.5)

        return charts

class Charts(QWidget):
    """
    Custom chart widget for displaying data.
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        super().setContentsMargins(4, 4, 4, 4)

        self.charts = pyqtgraph.PlotWidget(self)
        self.charts.setBackground('w')
        self.charts.showGrid(x=True, y=True, alpha=0.5)
        self.charts.showAxis('right', show=True)
        self.charts.showAxis('top', show=True)
        self.charts.getAxis('top').setStyle(showValues=False)
        self.charts.getAxis('right').setStyle(showValues=False)

        self.plot_data(
            [0, 1, 2, 3, 4],
            [0, 1, 4, 9, 16],
            "Time (h)",
            "Value (units)"
        )


        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.charts)
        self.setLayout(layout)

    def plot_data(self, x, y, x_label, y_label, title="Data Plot"):
        """
        Plot data on the chart.
        :param x: X-axis data.
        :param y: Y-axis data.
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the plot (default: "Data Plot").
        """

        self.charts.plot(x, y, pen=pyqtgraph.mkPen('black', width=2), symbol='+', symbolSize=8, symbolBrush='b')
        self.charts.setLabel('left', y_label)
        self.charts.setLabel('bottom', x_label)
        self.charts.setTitle(title, color='black', size='14pt')