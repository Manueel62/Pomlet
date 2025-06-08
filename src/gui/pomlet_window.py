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

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.config import get_subjects
from src.gui.tabs.add_flashcard import AddTab
from src.gui.tabs.list_flashcard import ListTab
from src.gui.tabs.review_flashcard import ReviewTab
from src.gui.tabs.timer.timer_tab import TimerTab
from src.gui.tray import Tray
from src.questions_manager import QuestionManager
from src.timer.pomlet_timer import PomletTimer


class PomletWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomlet")
        self.setFixedSize(400, 560)

        self._subjects = get_subjects()
        self._timer = PomletTimer()
        self._tray: Tray = Tray()

        self._questions_manager: QuestionManager = QuestionManager()
        self._to_repeat = self._questions_manager._questions_to_repeat
        self._add_tab: AddTab = AddTab(self._questions_manager)
        self._review_tab: ReviewTab = ReviewTab(self._questions_manager)
        self._list_tab: ListTab = ListTab(self._questions_manager)
        self._timer_tab: TimerTab = TimerTab(self._questions_manager, self._timer, self._tray)

        self._connect()
        self._build_tabs()
        self._tray.showMsg(
            f"Welcome back! There are {self._questions_manager.count()} flashcards to review today."
        )

    def _connect(self):
        # subjects signals
        self._timer_tab.subjects_updated.connect(self._add_tab.on_subjects_updated)
        self._timer_tab.subjects_updated.connect(self._list_tab.refresh)

        # flashcards signals
        self._add_tab.flashcard_added.connect(self._review_tab.on_flashcard_added)
        self._add_tab.flashcard_added.connect(self._list_tab.refresh)
        self._review_tab.flashcard_modified.connect(self._list_tab.refresh)
        self._add_tab.flashcard_added.connect(self._list_tab.refresh)

        # timer signals
        # tick sent to tray to be updated
        self._timer.tick.connect(self._timer_tab.on_tick)
        self._timer.ended.connect(self._timer_tab.on_session_ended)
        
        # self._timer.stopped.connect(self._timer_tab.on_session_stopped)
        # self._timer.started.connect(self._timer_tab.on_session_started)
        # self._timer.paused.connect(self._timer_tab.on_toggle_pause)

        self._tray.started.connect(self._timer_tab.on_session_started)
        self._tray.paused.connect(self._timer_tab.on_toggle_pause)
        self._tray.stopped.connect(self._timer_tab.on_session_stopped)

        # register tray actions
        # self._tray.start_signal.connect(self._timer_tab.start)
        # self._tray.pause_signal.connect(self._timer_tab.toggle_pause)
        # self._tray.stop_signal.connect(self._timer_tab.stop)

    def _build_tabs(self):
        self.setStyleSheet("""
        QPushButton {
            height: 18px
            }
        """)
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._timer_tab, "Timer")
        self.tabs.addTab(self._review_tab, "Review")
        self.tabs.addTab(self._add_tab, "Add")
        self.tabs.addTab(self._list_tab, "List")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def closeEvent(self, ev: QCloseEvent):
        self._questions_manager.save_questions()
        ev.accept()
