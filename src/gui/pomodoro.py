from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from src.gui.tabs.list_flashcard import ListTab
from src.config import get_subjects, load_config
from src.gui.tabs.add_flashcard import AddTab
from src.gui.tabs.review_flashcard import ReviewTab
from src.gui.tabs.timer.timer import TimerTab
from src.gui.tray import Tray
from src.questions_manager import QuestionManager


class PomodoroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomlet")
        self.setFixedSize(400, 560)

        self._subjects = get_subjects()
        self._tray: Tray = Tray()

        self._questions_manager: QuestionManager = QuestionManager()
        self._to_repeat = self._questions_manager._questions_to_repeat
        self._add_tab: AddTab = AddTab(self._questions_manager)
        self._review_tab: ReviewTab = ReviewTab(self._questions_manager)
        self._list_tab: ListTab = ListTab(self._questions_manager)
        default_work, default_break = load_config(None)
        self._timer_tab: TimerTab = TimerTab(
            self._questions_manager, self._tray, default_work, default_break
        )

        self._connect()
        self._build_tabs()
        self._tray.showMsg(
            f"Welcome back! There are {self._questions_manager.count()} flashcards to review today."
        )

    def _connect(self):
        self._timer_tab.subjects_updated.connect(self._add_tab.on_subjects_updated)
        self._add_tab.flashcard_added.connect(self._review_tab.on_flashcard_added)

        self._timer_tab.tick.connect(self._tray.update)
        self._tray.start_signal.connect(self._timer_tab.start)
        self._tray.pause_signal.connect(self._timer_tab.toggle_pause)
        self._tray.stop_signal.connect(self._timer_tab.stop)

        self._add_tab.flashcard_added.connect(self._list_tab.refresh)
        self._review_tab.flashcard_modified.connect(self._list_tab.refresh)
        self._add_tab.flashcard_added.connect(self._list_tab.refresh)

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
