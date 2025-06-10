"""
Pomlet - A simple Pomodoro timer for your studies.
Copyright (C) 2025 @ Manueel62

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLabel, QWidget

from src.timer.session_type import SessionType


class ProgressCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._percent = 0.0
        self._time_label: QLabel = QLabel("25:00")
        self._session_type: SessionType = SessionType.NONE
        self._n_sessions = 0
        self._icon = self._session_type_to_icon()

    def increase_n_sessions(self):
        self._n_sessions += 1
        self.update()

    def reset(self, text: str):
        self._percent = 0.0
        self._n_sessions = 0
        self._time_label.setText(text)
        self._session_type = SessionType.NONE
        self.update()

    def reset_icon(self):
        self._icon = self._session_type_to_icon()
        self.update()

    def set_icon(self, icon: str):
        print("ICON set to ", icon)        
        self._icon = icon
        self.update()

    def update_progress(self, percent: float, text: str):
        self._percent = percent
        self._time_label.setText(text)

        self.update()

    def _session_type_to_icon(self) -> str:
        match self._session_type:
            case SessionType.WORK:
                return "📚"
            case SessionType.BREAK:
                return "☕"
            case SessionType.NONE:
                return ""
            case SessionType.LONG_BREAK:
                return "☕☕"
            
    def update_session_type(self, session_type: SessionType):
        self._session_type = session_type
        self._icon = self._session_type_to_icon()
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 10
        rect = QRectF(
            margin, margin, self.width() - 2 * margin, self.height() - 2 * margin
        )
        not_color = QColor("#4a4a4a")
        done_color = QColor("#cccccc")

        painter.setPen(QPen(not_color, 8))
        painter.drawEllipse(rect)

        dot_radius = 2
        center_x = self.width() // 2
        center_y = self.height() // 2 + 70  # adjust distance below the time


        painter.setBrush(not_color)
        for i in range(self._n_sessions, 4):
            painter.drawEllipse(
                (center_x - dot_radius) + int((i - 1.5)*20),
                center_y - dot_radius,
                dot_radius * 2,
                dot_radius * 2
            )

        painter.setPen(QPen(done_color, 8))
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self._percent))

        font = QFont("Helvetica Neue", 30, QFont.Weight.Bold)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        painter.setFont(font)

        painter.drawText(
            self.rect().adjusted(0, 30, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self._icon,
        )

        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, self._time_label.text()
        )

        painter.setBrush(done_color)

        for i in range(0, self._n_sessions):
            painter.drawEllipse(
                (center_x - dot_radius) + int((i - 1.5)*20),
                center_y - dot_radius,
                dot_radius * 2,
                dot_radius * 2
            )
    
    @property
    def n_sessions(self):
        return self._n_sessions