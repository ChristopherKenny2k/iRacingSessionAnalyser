from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtCore import Qt


class ColorDelegate(QStyledItemDelegate):
    """used in colouring of specific cells to denote inllap/outlap/fastest lap"""

    def paint(self, painter, option, index):
        bg_color = index.data(Qt.ItemDataRole.BackgroundRole)

        if bg_color:
            painter.fillRect(option.rect, bg_color)

        super().paint(painter, option, index)
