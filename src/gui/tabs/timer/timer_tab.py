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
from datetime import datetime
from typing import Callable, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.calendar_manager import create_calendar_event
from src.config import (
    add_subject,
    get_subjects,
    load_config,
    modify_subject,
    remove_subject,
)
from src.gui.tabs.timer.progress_circle import ProgressCircle
from src.gui.tray import Tray
from src.questions_manager import QuestionManager
from src.sound import play_sound
from src.timer.pomlet_timer import PomletTimer, SessionType

logger = logging.getLogger(__name__)


class TimerTab(QWidget):
    subjects_updated = Signal(str)

    def __init__(
        self, questions_manager: QuestionManager, timer: PomletTimer, tray: Tray
    ):
        super().__init__()

        default_work, default_break = load_config(None)

        self._default_work: int = default_work
        self._default_break: int = default_break
        self._timer = timer
        self._tray = tray

        self._questions_manager: QuestionManager = questions_manager
        self._subjects: List[str] = get_subjects()
        self._subject_box = QComboBox()
        self._add_btn = QPushButton("+")
        self._rm_btn = QPushButton("-")

        self._work_started_at = None
        self._work_done: bool = False

        self._work_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self._break_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self._work_value_label: QLabel = QLabel()
        self._break_value_label: QLabel = QLabel()

        self._start_btn = QPushButton("▶ Start")
        self._stop_btn = QPushButton("■ Stop")
        self._pause_btn = QPushButton("⏸ Pause")
        self._circle = ProgressCircle()

        self._build()
        self._reset()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        row = QHBoxLayout()
        row.addWidget(QLabel("Subject:"))
        self._subject_box.setFixedHeight(30)
        self._subject_box.setFixedWidth(130)
        self._subject_box.addItems(self._subjects)
        if self._subject_box.count() == 0:
            self._rm_btn.setEnabled(False)

        self._subject_box.currentIndexChanged.connect(self.on_subject_changed)

        if len(self._subjects) > 0:
            self._subject_box.setCurrentText(self._subjects[0])
            self._default_work, self._default_break = load_config(self._subjects[0])

        row.addWidget(self._subject_box)
        self._add_btn.setFixedSize(40, 30)
        self._rm_btn.setFixedSize(40, 30)

        self._add_btn.clicked.connect(self._add_subject)
        self._rm_btn.clicked.connect(self._remove_subject)

        row.addWidget(self._add_btn)
        row.addWidget(self._rm_btn)
        layout.addLayout(row)

        self._circle.setFixedSize(240, 240)
        layout.addWidget(self._circle, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(
            self._make_slider(
                self._work_slider,
                QLabel("Work Duration:"),
                self._work_value_label,
                self._default_work,
                1,
                60,
                self._work_changed,
            )
        )
        layout.addLayout(
            self._make_slider(
                self._break_slider,
                QLabel("Break Duration:"),
                self._break_value_label,
                self._default_break,
                1,
                30,
                self._break_changed,
            )
        )

        btns: QHBoxLayout = QHBoxLayout()
        self._start_btn.setObjectName("Start")
        self._start_btn.clicked.connect(self.on_session_started)

        self._stop_btn.setObjectName("Stop")
        self._stop_btn.clicked.connect(self.on_session_stopped)

        self._pause_btn.setObjectName("Pause")
        self._pause_btn.clicked.connect(self.on_toggle_pause)

        for btn in [self._start_btn, self._stop_btn, self._pause_btn]:
            btn.setMinimumWidth(80)

        btns.addWidget(self._start_btn)
        btns.addWidget(self._stop_btn)
        btns.addWidget(self._pause_btn)
        layout.addLayout(btns)

    def _remove_subject(self):
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Removing Subject",
            f"Are you sure you want to delete '{self._subject_box.currentText()}' and all its flashcards?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        logging.debug(f"Removing subject: {self._subject_box.currentText()}")
        if reply == QMessageBox.StandardButton.No:
            logging.debug("Subject not removed. User cancelled.")
            return

        remove_subject(self._subject_box.currentText())
        self._questions_manager.remove_all_by_subject(self._subject_box.currentText())

        self._subject_box.removeItem(self._subject_box.currentIndex())
        if self._subject_box.count() > 0:
            self._subject_box.setCurrentIndex(0)
        else:
            self._rm_btn.setEnabled(False)

        self.subjects_updated.emit(self._subject_box.currentText())

    def _add_subject(self):
        subject_name: str
        ok: bool

        subject_name, ok = QInputDialog.getText(self, "Add Subject", "Subject Name:")
        subject_name = subject_name.strip()

        if ok and subject_name:
            if subject_name.strip() == "":
                QMessageBox.warning(
                    self, "Invalid Subject Name", "Subject name cannot be empty!"
                )
                return

            add_subject(subject_name)
            self._subject_box.addItem(subject_name)  # timer tab
            self._subject_box.setCurrentText(subject_name)

            # update add tab box
            self.subjects_updated.emit(subject_name)
            self._rm_btn.setEnabled(True)

    def on_session_started(self):
        if self._subject_box.currentText() == "":
            QMessageBox.warning(
                self, "No Subject Selected", "Please create a subject first!"
            )
            logger.debug("No subject selected. Aborting.")
            return

        if self._work_done:
            self._timer.start_session(SessionType.BREAK, self._break_slider.value())
            self._work_done = False
        else:
            self._timer.start_session(SessionType.WORK, self._work_slider.value())

        logger.debug("Starting timer in %s", self._timer.current_session_type())

        self._work_started_at = datetime.now()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._pause_btn.setEnabled(True)
        self._work_slider.setEnabled(False)
        self._break_slider.setEnabled(False)
        self._subject_box.setEnabled(False)
        self._add_btn.setEnabled(False)
        self._rm_btn.setEnabled(False)
        self._tray.on_session_started()

    def on_session_stopped(self):
        logger.debug("Reacting to timer being stopped")
        self._timer.stop()
        self._reset()
        self._tray.on_session_stopped()

    def on_toggle_pause(self):
        logger.debug("Toggling pause, current state: %s", self._timer.is_paused())
        if self._timer.is_paused():
            self._timer.resume()
            self._pause_btn.setText("⏸ Pause")
            self._tray.on_toggle_pause()
        else:
            self._timer.pause()
            self._pause_btn.setText("▶ Resume")
            self._tray.on_toggle_pause()

    def on_tick(self, perc: float, mins: int, secs: int):
        self._update_circle(perc, mins, secs)
        self._tray.on_tick(perc, mins, secs)

    def _update_circle(self, perc: float, mins: int, secs: int):
        time_to_display: str = f"{mins:02}:{secs:02}"
        self._circle.update_progress(perc, time_to_display)

    def on_session_ended(self):
        msg: str = ""

        play_sound()

        match self._timer.current_session_type():
            case SessionType.WORK:
                msg = "Time's up! Take a break!"
                self._work_done = True
                title = f"{self._subject_box.currentText()} Pomodoro"
                create_calendar_event(title, self._work_started_at, datetime.now())
                self._start_btn.setText("▶ Start Break")
                self._circle.update_progress(1, f"{self._break_slider.value()}:00")
                self._tray.on_session_ended(SessionType.BREAK)
            case SessionType.BREAK:
                msg = "Time's up! Get back to work!"
                self._start_btn.setText("▶ Start")
                self._circle.update_progress(1, f"{self._break_slider.value()}:00")
                self._tray.on_session_ended(SessionType.WORK)

            case _:
                logger.warning("Tried to end session, but no session running!")
                return

        self._tray.showMessage("Pomlet", msg, QSystemTrayIcon.MessageIcon.Information)
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._work_slider.setEnabled(True)
        self._break_slider.setEnabled(True)
        self._subject_box.setEnabled(True)

    def on_subject_changed(self):
        logger.debug("Subject changed in TimerTab")
        subject: str = self._subject_box.currentText()
        self.subjects_updated.emit(subject)

        self._default_work, self._default_break = load_config(subject)

        self._work_slider.setValue(self._default_work)
        self._break_slider.setValue(self._default_break)

        self._work_value_label.setText(f"{self._default_work} min")
        self._break_value_label.setText(f"{self._default_break} min")

        if self._timer.current_session_type() is not SessionType.NONE:
            self._circle.reset(f"{self._default_work:02}:00")

    def _make_slider(
        self,
        slider: QSlider,
        label: QLabel,
        value_label: QLabel,
        default: int,
        min_: int,
        max_: int,
        cb: Callable,
    ):
        layout = QHBoxLayout()
        slider.setRange(min_, max_)
        slider.setValue(default)
        slider.valueChanged.connect(cb)

        value_label.setText(f"{default} min")
        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addWidget(value_label)

        return layout

    def _reset(self):
        self._work_done = False

        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶ Start")
        self._stop_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setText("⏸ Pause")

        self._subject_box.setEnabled(True)
        self._work_slider.setEnabled(True)
        self._break_slider.setEnabled(True)
        self._add_btn.setEnabled(True)
        self._rm_btn.setEnabled(True)

        self._circle.reset(f"{self._work_slider.value():02}:00")

    def _work_changed(self, val: int):
        self._work_value_label.setText(f"{val} min")
        if self._timer.current_session_type() is SessionType.NONE and not self._work_done:
            self._circle.reset(f"{val:02}:00")
        modify_subject(self._subject_box.currentText(), val, self._break_slider.value())

    def _break_changed(self, val):
        self._break_value_label.setText(f"{val} min")
        if self._timer.current_session_type() is SessionType.NONE and self._work_done:
            self._circle.reset(f"{val:02}:00")
        modify_subject(self._subject_box.currentText(), self._work_slider.value(), val)
