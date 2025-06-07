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

import logging
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QMessageBox, QSystemTrayIcon

import src.gui.assets  # tray icon

logger = logging.getLogger(__name__)


class Tray(QSystemTrayIcon):
    start_signal = Signal()
    stop_signal = Signal()
    pause_signal = Signal()

    def __init__(self):
        super().__init__()

        logger.debug("Tray path: %s", Path().absolute())
        self._initial_icon: QIcon = QIcon(":/tray_icon.png")
        self._menu: QMenu = QMenu()

        # actions
        self._time_left = QAction("")
        self._start_timer = QAction("Start")
        self._pause_timer = QAction("Pause")
        self._stop_timer = QAction("Stop")
        self._about = QAction("About...")
        self._quit = QAction("Quit")

        self._build()

    def _show_about(self):
        QMessageBox.about(
            None,
            "About Pomlet",
            """
            <b>Pomlet</b><br>
            A simple Pomodoro timer for your studies.<br><br>
            <b>Version:</b> 0.0.3<br>
            <b>Author:</b> Manueel62 <br>
            <b>Website:</b> <a href='https://github.com/manueel62/pomlet'>https://github.com/manueel62/pomlet</a><br><br>
            GPL License © 2025 Manueel62. All rights reserved.
            """,
        )

    def _build(self):
        self.setIcon(self._initial_icon)
        self.setVisible(True)
        self._time_left.setVisible(False)

        self._pause_timer.setEnabled(False)

        # connect actions
        self._quit.triggered.connect(QApplication.quit)
        self._about.triggered.connect(self._show_about)
        self._start_timer.triggered.connect(self.start)
        self._pause_timer.triggered.connect(self.pause)
        self._stop_timer.triggered.connect(self.stop)

        # add actions
        self._menu.addAction(self._time_left)
        self._menu.addAction(self._start_timer)
        self._menu.addAction(self._pause_timer)
        self._menu.addAction(self._stop_timer)
        self._menu.addAction(self._about)
        self._menu.addAction(self._quit)

        # Add the menu to the tray
        self.setContextMenu(self._menu)

    def start(self):
        self._time_left.setVisible(True)

        self.start_signal.emit()
        self._start_timer.setEnabled(False)
        self._pause_timer.setEnabled(True)
        self._stop_timer.setEnabled(True)

    def stop(self):
        self._time_left.setVisible(False)

        self.stop_signal.emit()
        self._start_timer.setEnabled(True)
        self._pause_timer.setEnabled(False)
        self._stop_timer.setEnabled(False)

    def pause(self):
        self.pause_signal.emit()
        self._pause_timer.setText(
            "Resume" if self._pause_timer.text() == "Pause" else "Pause"
        )

    def update(self, remaining_minutes: int, remaining_seconds: int):
        self.setIcon(self.label_to_icon(QLabel(f"{remaining_minutes}")))
        self._time_left.setText(
            f"Time left: {remaining_minutes:02}:{remaining_seconds:02}"
        )

    def label_to_icon(self, label: QLabel, render_size: int = 64) -> QIcon:
        # Style and layout
        label.setStyleSheet("""
            QLabel {
                background: transparent;
                font: bold 40px;
            }
        """)
        label.setFixedSize(QSize(render_size, render_size))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        pixmap = QPixmap(render_size, render_size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        label.render(
            painter,
            QPoint(0, 0),
            QRegion(label.rect()),
        )
        painter.end()

        return QIcon(pixmap)

    def showMsg(self, msg: str):
        if sys.platform == "darwin":
            subprocess.run(
                ["osascript", "-e", f'display notification "{msg}" with title "Pomlet"']
            )
        self.showMessage("Pomlet", msg, QSystemTrayIcon.MessageIcon.Information)
        if sys.platform == "darwin":
            subprocess.run(
                ["osascript", "-e", f'display notification "{msg}" with title "Pomlet"']
            )
        self.showMessage("Pomlet", msg, QSystemTrayIcon.MessageIcon.Information)
