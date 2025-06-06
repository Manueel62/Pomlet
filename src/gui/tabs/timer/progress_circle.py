from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget, QLabel


class ProgressCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._percent = 0.0
        self._time_label: QLabel = QLabel("25:00")

    def reset(self, text: str):
        self._percent = 0.0
        self._time_label.setText(text)
        self.update()

    def update_progress(self, percent: float, text: str):
        self._percent = percent
        self._time_label.setText(text)

        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 10
        rect = QRectF(
            margin, margin, self.width() - 2 * margin, self.height() - 2 * margin
        )

        painter.setPen(QPen(QColor("#cccccc"), 8))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor("#4a4a4a"), 8))
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self._percent))

        font = QFont("Helvetica Neue", 30, QFont.Weight.Bold)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._time_label.text())
