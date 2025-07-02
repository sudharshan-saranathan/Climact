from util import load_svg
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsItemGroup
)

class Folder(QGraphicsItemGroup):

    # Constructor:
    def __init__(self, items: list, parent: QGraphicsItem | None = None):

        super().__init__(parent)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        super().setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._icon = load_svg("rss/icons/folder.svg", width=64)
        self._rect = QRectF(-48, -48, 96, 96)

        for item in items:
            self.addItem(item)

    def boundingRect(self):
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = QPixmap("rss/icons/folder.svg")
        pixmap = pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        painter.drawPixmap(self._rect.topLeft(), pixmap)