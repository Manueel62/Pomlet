import enum
import logging
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
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
from src.questions_manager import QuestionManager
from src.sound import play_sound

logger = logging.getLogger(__name__)


class SessionType(enum.Enum):
    BREAK = enum.auto()
    WORK = enum.auto()
    NONE = enum.auto()


class TimerTab(QWidget):
    subjects_updated = Signal(str)

    def __init__(
        self,
        questions_manager: QuestionManager,
        tray: QSystemTrayIcon,
        default_work: int,
        default_break: int,
    ):
        super().__init__()

        self._default_work: int = default_work
        self._default_break: int = default_break

        # with open("src/gui/style.css") as f:
        #     self.setStyleSheet(f.read())

        self._questions_manager: QuestionManager = questions_manager
        self._tray: QSystemTrayIcon = tray
        self._subjects: List[str] = get_subjects()
        self._subject_box = QComboBox()
        self._add_btn = QPushButton("+")
        self._rm_btn = QPushButton("-")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._current_session_type: SessionType = SessionType.NONE
        self._total_time: timedelta = timedelta()
        self._remaining_time: timedelta = timedelta()
        self._session_end_time: Optional[datetime] = None
        self._work_started_at = None
        self._work_done: bool = False
        self._paused: bool = False

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
        self._start_btn.clicked.connect(self._start_work)

        self._stop_btn.setObjectName("Stop")
        self._stop_btn.clicked.connect(self._stop_session)

        self._pause_btn.setObjectName("Pause")
        self._pause_btn.clicked.connect(self._pause_resume)

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
            f"Are you sure you want to delete '{self._subject_box.currentText()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply is QMessageBox.StandardButton.No:
            return

        remove_subject(self._subject_box.currentText())
        self._subject_box.removeItem(self._subject_box.currentIndex())
        self.subjects_updated.emit(None)

    def _add_subject(self):
        subject_name: str
        ok: bool

        subject_name, ok = QInputDialog.getText(self, "Add Subject", "Subject Name:")
        subject_name = subject_name.strip()

        if ok and subject_name:
            add_subject(subject_name)
            self._subject_box.addItem(subject_name)  # timer tab
            self._subject_box.setCurrentText(subject_name)

            # update add tab box
            self.subjects_updated.emit(subject_name)

    def _start_work(self):
        if (
            self._work_done
            and self._start_btn.text().lower().strip() == "▶ start break"
        ):
            self._start_break()
        else:
            self._start_session(SessionType.WORK, self._work_slider.value())
            self._work_started_at = datetime.now()

    def _start_break(self):
        self._start_session(SessionType.BREAK, self._break_slider.value())

    def _start_session(self, session_type: SessionType, minutes: int):
        if self._session_end_time is not None:
            logger.warning("Tried to start a session, but already existing!")
            return

        self._current_session_type = session_type
        self._total_time = timedelta(minutes=minutes)
        self._session_end_time = datetime.now() + self._total_time
        self._remaining_time = self._total_time
        self._paused = False

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._pause_btn.setEnabled(True)

        self._work_slider.setEnabled(False)
        self._break_slider.setEnabled(False)
        self._subject_box.setEnabled(False)

        self._update_circle()
        self._timer.start(1000)

    def _stop_session(self):
        self._reset()

    def _pause_resume(self):
        if self._paused:
            self._session_end_time = datetime.now() + self._remaining_time
            self._timer.start(1000)
            self._pause_btn.setText("⏸ Pause")
        else:
            if self._session_end_time is None:
                logger.warning("Tried to pause, but no session running!")
                return

            self._remaining_time = self._session_end_time - datetime.now()
            self._timer.stop()
            self._pause_btn.setText("▶ Resume")
        self._paused = not self._paused

    def _tick(self):
        if self._session_end_time is None:
            logger.warning("Tried to tick, but no session running!")
            return

        self._remaining_time = self._session_end_time - datetime.now()
        if self._remaining_time.total_seconds() <= 0:
            self._timer.stop()
            self._session_done()
            return
        self._update_circle()

    def _update_circle(self):
        total_secs = int(self._remaining_time.total_seconds())
        mins, secs = divmod(total_secs, 60)
        percent = 1 - self._remaining_time / self._total_time
        self._circle.update_progress(percent, f"{mins:02}:{secs:02}")

    def _session_done(self):
        play_sound()
        self._tray.showMessage(
            "Pomodoro", "Time's up!", QSystemTrayIcon.MessageIcon.Information
        )

        if self._current_session_type == "work":
            self._work_done = True
            title = f"{self._subject_box.currentText()} Pomodoro"
            create_calendar_event(title, self._work_started_at, datetime.now())
            self._start_btn.setText("▶ Start Break")
        else:
            self._start_btn.setText("▶ Start Work")

        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._work_slider.setEnabled(True)
        self._break_slider.setEnabled(True)
        self._subject_box.setEnabled(True)

        self._current_session_type = SessionType.NONE

    def on_subject_changed(self):
        subject: str = self._subject_box.currentText()
        self.subjects_updated.emit(subject)

        self._default_work, self._default_break = load_config(subject)

        self._work_slider.setValue(self._default_work)
        self._break_slider.setValue(self._default_break)

        self._work_value_label.setText(f"{self._default_work} min")
        self._break_value_label.setText(f"{self._default_break} min")

        if not self._current_session_type:
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
        self._timer.stop()
        self._current_session_type = SessionType.NONE
        self._work_done = False
        self._paused = False
        self._session_end_time = None

        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶ Start")
        self._stop_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setText("⏸ Pause")

        self._subject_box.setEnabled(True)
        self._work_slider.setEnabled(True)
        self._break_slider.setEnabled(True)

        self._circle.reset(f"{self._work_slider.value():02}:00")

    def _work_changed(self, val: int):
        self._work_value_label.setText(f"{val} min")
        if self._current_session_type is SessionType.NONE:
            self._circle.reset(f"{val:02}:00")
        modify_subject(self._subject_box.currentText(), val, self._break_slider.value())

    def _break_changed(self, val):
        self._break_value_label.setText(f"{val} min")
        modify_subject(self._subject_box.currentText(), self._work_slider.value(), val)
