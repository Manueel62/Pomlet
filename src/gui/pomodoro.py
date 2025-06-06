import subprocess

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QStyle, QSystemTrayIcon, QTabWidget, QVBoxLayout, QWidget

from src.config import get_subjects, load_config
from src.gui.tabs.add_flashcard import AddTab
from src.gui.tabs.review_flashcard import ReviewTab
from src.gui.tabs.timer.timer import TimerTab
from src.questions_manager import QuestionManager


def notify_macos(title: str, message: str):
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "{title}"']
    )


class PomodoroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomlet")
        # self.setFixedSize(360, 560)
        self.setFixedSize(400, 560)

        self.subjects = get_subjects()

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        )
        self.tray.setToolTip("Pomlet")
        self.tray.show()

        # with open("src/gui/style.css") as f:
        #     self.setStyleSheet(f.read())

        self._questions_manager = QuestionManager()
        self._to_repeat = self._questions_manager._questions_to_repeat
        self._build_tabs()
        notify_macos("Pomodoro Timer", "Time left: 25:00")

    def _build_tabs(self):
        default_work, default_break = load_config(None)

        add_tab: QWidget = AddTab(self._questions_manager)
        review_tab: QWidget = ReviewTab(self._questions_manager)
        timer_tab: QWidget = TimerTab(
            self._questions_manager, self.tray, default_work, default_break
        )
        timer_tab.subjects_updated.connect(add_tab.on_subjects_updated)
        add_tab.flashcard_added.connect(review_tab.on_flashcard_added)
        self.tabs = QTabWidget(self)

        self.tabs.addTab(timer_tab, "Timer")
        self.tabs.addTab(review_tab, "Review")
        self.tabs.addTab(add_tab, "Add")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def closeEvent(self, ev: QCloseEvent):
        self._questions_manager.save_questions()
        ev.accept()
