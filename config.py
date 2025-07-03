import os
import platform

from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtCore import QPointF, QRectF, QLineF, Qt

ClimactConfig = {
    "font"  : QFont("Trebuchet MS", 13 if platform.system() == "Darwin" else 10),
    "root"  : os.path.dirname(os.path.abspath(__file__)),
    "style" : os.path.dirname(os.path.abspath(__file__)) + "/rss/style/macos.qss"
}

ViewerConfig = {
    "zoom"  : 1.0,
}

# Node's default configuration:
NodeDefaultConfig = {
    "nuid"  :   str(),                                          # Unique identifier for the node.
    "name"  :   str(),                                          # Name of the node.
    "npos"  :   QPointF(0, 0),                                  # Node's scene-position.
    "rect"  :   QRectF(-100, -75, 200, 150),                    # Node's bounding rectangle.
    "step"  :   50,
    "border":   QColor(0x0),                                    # Color of the node's border when not selected.
    "select":   QColor(0xffa347),                               # Color of the node's border when selected.
    "color" :   QColor(0xffffff),                               # Background color of the node.
    "hover" :   QColor(0xefefef),                               # Background color of the node when hovered.
}

AnchorDefaultConfig = {
    "dims"  :   QLineF( 0, -40,  0,  64),                           # Vertical line from (-40, 0) to (68, 0)
    "rect"  :   QRectF(-5, -40, 10, 108),                           # Rectangle bounding the anchor.
    "pen"   :   QPen(QColor(0x006d8f), 3.0, Qt.PenStyle.SolidLine), # Pen color of the anchor.
    "inp"   :   QPointF(NodeDefaultConfig["rect"].left()  + 5, 0),  # Position of the input anchor.
    "out"   :   QPointF(NodeDefaultConfig["rect"].right() - 5, 0),  # Position of the output anchor.
}

# Handle's default configuration:
HandleDefaultConfig = {
    "rect"  :   QRectF(-2.0, -2.0, 4, 4),                           # Rectangle bounding the handle.
    "pen"   :   QPen(QColor(0x0), 0.75),                            # Pen color of the handle's border.
    "color" :   QColor(0xcfffb3),
    "hint-rect" : QRectF(-0.75, -0.75, 1.5, 1.5),                   # Rectangle bounding the handle's hint.
    "hint-color": QColor(0x0),                                      # Color of the handle's hint.
}