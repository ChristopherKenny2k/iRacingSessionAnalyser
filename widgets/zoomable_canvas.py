from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ZoomableCanvas(FigureCanvas):
    """matplotlib canvas that supports mouse-wheel zoom and click-drag pan
    on its first (and only expected) axes."""

    def __init__(self, fig):
        super().__init__(fig)
        self._pressing = False
        self._last_x = None
        self._last_y = None

    def wheelEvent(self, event):
        ax = self.figure.axes[0]

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        x_data = (xlim[0] + xlim[1]) / 2
        y_data = (ylim[0] + ylim[1]) / 2

        zoom_factor = 0.85 

        if event.angleDelta().y() > 0:
            scale = zoom_factor
        else:
            scale = 1 / zoom_factor

        new_xlim = [
            x_data + (xlim[0] - x_data) * scale,
            x_data + (xlim[1] - x_data) * scale
        ]
        new_ylim = [
            y_data + (ylim[0] - y_data) * scale,
            y_data + (ylim[1] - y_data) * scale
        ]

        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        self.draw()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressing = True
            self._last_x = event.position().x()
            self._last_y = event.position().y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressing = False
            self._last_x = None
            self._last_y = None

    def mouseMoveEvent(self, event):
        if self._pressing and self._last_x is not None:
            ax = self.figure.axes[0]
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            dx = event.position().x() - self._last_x
            dy = event.position().y() - self._last_y

            x_scale = (xlim[1] - xlim[0]) / self.width()
            y_scale = (ylim[1] - ylim[0]) / self.height()

            ax.set_xlim(xlim[0] - dx * x_scale, xlim[1] - dx * x_scale)
            ax.set_ylim(ylim[0] + dy * y_scale, ylim[1] + dy * y_scale)

            self._last_x = event.position().x()
            self._last_y = event.position().y()

            self.draw()
