from datetime import datetime, timedelta

from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter, QPen
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.calendar_manager import create_calendar_event
from src.config import (
    add_subject,
    get_subjects,
    load_config,
    modify_subject,
    save_config,
)
from src.questions_manager import QuestionManager
from src.sound import play_sound


def _write_config(work, brk, sess):
    save_config(work, brk, sess)


# ---------------------------- Circle Display ----------------------------- #
class ProgressCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._percent = 0.0
        self._text = "25:00"

    def reset(self, text):
        self._percent, self._text = 0.0, text
        self.update()

    def update_progress(self, percent, text):
        self._percent, self._text = percent, text
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = 10
        rect = QRectF(
            margin, margin, self.width() - 2 * margin, self.height() - 2 * margin
        )

        painter.setPen(QPen(QColor("#cccccc"), 8))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor("#4a4a4a"), 8))
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self._percent))

        painter.setPen(QColor(255, 255, 255))
        font = QFont("Helvetica Neue", 30, QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)


# ------------------------------ Main App ------------------------------- #
class PomodoroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro Timer")
        self.setFixedSize(360, 560)

        self.subjects = get_subjects()
        self.default_work, self.default_break = load_config(None)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self.current_session = None
        self.total_time = timedelta()
        self.remaining_time = timedelta()
        self.session_end_time = None
        self.work_started_at = None
        self.work_done = False
        self.paused = False

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.show()

        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #666;
                border: 1px solid #555;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 5px;
            }
        """)

        self.start_review_btn = QPushButton("Start")
        self.ok_btn = QPushButton("OK")
        self.wrong_btn = QPushButton("X")

        self._questions_manager = QuestionManager()
        self._to_repeat = self._questions_manager.questions_to_repeat
        self._build_tabs()
        self._reset()

    def _build_tabs(self):
        self.tabs = QTabWidget(self)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.tabs.addTab(self.tab1, "Timer")
        self.tabs.addTab(self.tab2, "Review")
        self.tabs.addTab(self.tab3, "Add")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

        self._build_ui(parent=self.tab1)
        self._build_review_tab()
        self._build_add_tab()

    def _build_add_tab(self):
        layout = QVBoxLayout(self.tab3)
        add_layout = QHBoxLayout()

        self.subject_dropdown = QComboBox()
        self.subject_dropdown.addItems(self.subjects[:])
        self.subject_dropdown.setFixedWidth(200)

        self.add_flashcard_btn = QPushButton("+")
        self.add_flashcard_btn.setToolTip("Add a new flashcard")
        self.add_flashcard_btn.setFixedSize(40, 30)
        self.add_flashcard_btn.clicked.connect(self._on_add_flashcard_clicked)

        add_layout.addWidget(self.subject_dropdown)
        add_layout.addWidget(self.add_flashcard_btn)
        add_layout.addStretch()

        input_layout = QVBoxLayout()
        self.question_input = QTextEdit()
        self.question_input.setFixedHeight(100)
        self.add_info_label = QLabel("")

        input_layout.addLayout(add_layout)
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.add_info_label)

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)  # Ctrl+Q shortcut
        shortcut.activated.connect(self._on_add_flashcard_clicked)

        layout.addLayout(input_layout)

    def _build_ui(self, parent=None):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)

        row = QHBoxLayout()
        row.addWidget(QLabel("Subject:"))
        self.subject_box = QComboBox()
        self.subject_box.setFixedHeight(30)
        self.subject_box.setFixedWidth(130)
        self.subject_box.addItems(self.subjects)
        self.subject_box.currentIndexChanged.connect(self.on_subject_changed)

        if len(self.subjects) > 0:
            self.subject_box.setCurrentText(self.subjects[0])
            self.default_work, self.default_break = load_config(self.subjects[0])

        row.addWidget(self.subject_box)

        add_btn = QPushButton("+")
        rm_btn = QPushButton("-")
        add_btn.setFixedSize(40, 30)
        rm_btn.setFixedSize(40, 30)

        add_btn.clicked.connect(self._add_subject)
        rm_btn.clicked.connect(self._rm_session_type)

        row.addWidget(add_btn)
        row.addWidget(rm_btn)
        layout.addLayout(row)

        self.circle = ProgressCircle()
        self.circle.setFixedSize(240, 240)
        layout.addWidget(self.circle, alignment=Qt.AlignCenter)

        layout.addLayout(
            self._make_slider(
                "Work Duration:", self.default_work, 1, 60, self._work_changed
            )
        )
        layout.addLayout(
            self._make_slider(
                "Break Duration:", self.default_break, 1, 30, self._break_changed
            )
        )

        btns = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("Start")
        self.start_btn.clicked.connect(self._start_work)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("Stop")
        self.stop_btn.clicked.connect(self._stop_session)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setObjectName("Pause")
        self.pause_btn.clicked.connect(self._pause_resume)

        for btn in [self.start_btn, self.stop_btn, self.pause_btn]:
            btn.setMinimumWidth(80)

        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.pause_btn)
        layout.addLayout(btns)

    def _build_review_tab(self):
        layout = QVBoxLayout(self.tab2)

        # Title label for the subject
        self.subject_label = QLabel()
        self.subject_label.setText(f"Course: {self._questions_manager.get_subject()}")
        self.subject_label.setAlignment(Qt.AlignCenter)
        self.subject_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            margin: 15px;
        """)
        layout.addWidget(self.subject_label)

        # Flashcard count label
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setText(
            f"There are {self._questions_manager.count()} flashcards to review"
        )
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            margin: 10px;
        """)
        layout.addWidget(self.question_label)

        # Buttons layout (review controls)
        btns = QHBoxLayout()

        self.ok_btn.setEnabled(False)
        self.wrong_btn.setEnabled(False)

        self.ok_btn.clicked.connect(self._on_ok_clicked)
        self.start_review_btn.clicked.connect(self._on_start_review)
        self.wrong_btn.clicked.connect(self._on_cancel_clicked)

        btns.addWidget(self.ok_btn)
        btns.addWidget(self.start_review_btn)
        btns.addWidget(self.wrong_btn)
        layout.addLayout(btns)

    def on_subject_changed(self):
        subject = self.subject_box.currentText()
        self.subject_dropdown.setCurrentText(subject)

        self.default_work, self.default_break = load_config(subject)

        self.work_slider.setValue(self.default_work)
        self.break_slider.setValue(self.default_break)

        self.work_val.setText(f"{self.default_work} min")
        self.break_val.setText(f"{self.default_break} min")

        if not self.current_session:
            self.circle.reset(f"{self.default_work:02}:00")

    def _on_add_flashcard_clicked(self):
        if self.question_input.toPlainText().strip() == "":
            return

        question = self._questions_manager.add_question(
            self.question_input.toPlainText(), self.subject_dropdown.currentText()
        )

        if question is None:
            self.add_info_label.setText("Error while adding question")
        else:
            self.add_info_label.setText(f"Question added: ID {question['id']}")
        self.question_input.setText("")

        # update count in review
        self.question_label.setText(
            f"There are {self._questions_manager.count()} flashcards to review"
        )

    def _on_ok_clicked(self):
        self._questions_manager.correct()
        q = self._questions_manager.get_next_to_repeat()
        if q is None:
            self.question_label.setText("Done")
            self.ok_btn.setEnabled(False)
            self.wrong_btn.setEnabled(False)
            return

        self.question_label.setText(q["question"])
        self.subject_label.setText(q["subject"])

    def _on_start_review(self):
        self.ok_btn.setEnabled(True)
        self.wrong_btn.setEnabled(True)
        self.start_review_btn.setEnabled(False)
        q = self._questions_manager.get_next_to_repeat()

        if q is None:
            self.question_label.setText("Done")
            self.ok_btn.setEnabled(False)
            self.wrong_btn.setEnabled(False)
            return

        self.question_label.setText(q["question"])
        self.subject_label.setText(q["subject"])


    def _on_cancel_clicked(self):
        self._questions_manager.wrong()
        q = self._questions_manager.get_next_to_repeat()

        if q is None:
            self.question_label.setText("Done")
            self.ok_btn.setEnabled(False)
            self.wrong_btn.setEnabled(False)
            return

        self.question_label.setText(q["question"])
        self.subject_label.setText(q["subject"])

    def _make_slider(self, label, default, mn, mx, slot):
        layout = QHBoxLayout()
        lbl = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(mn, mx)
        slider.setValue(default)
        slider.valueChanged.connect(slot)
        val = QLabel(f"{default} min")
        layout.addWidget(lbl)
        layout.addWidget(slider)
        layout.addWidget(val)

        if "Work" in label:
            self.work_slider, self.work_val = slider, val
        else:
            self.break_slider, self.break_val = slider, val
        return layout

    def _reset(self):
        self.timer.stop()
        self.current_session = None
        self.work_done = False
        self.paused = False

        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶ Start")
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause")

        self.subject_box.setEnabled(True)
        self.work_slider.setEnabled(True)
        self.break_slider.setEnabled(True)

        self.circle.reset(f"{self.work_slider.value():02}:00")

    def _work_changed(self, val):
        self.work_val.setText(f"{val} min")
        if not self.current_session:
            self.circle.reset(f"{val:02}:00")
        modify_subject(self.subject_box.currentText(), val, self.break_slider.value())

    def _break_changed(self, val):
        self.break_val.setText(f"{val} min")
        modify_subject(self.subject_box.currentText(), self.work_slider.value(), val)

    def _add_subject(self):
        subject_name, ok = QInputDialog.getText(self, "Add Subject", "Subject Name:")
        subject_name = subject_name.strip()
        if ok and subject_name:
            if subject_name not in self._session_list():
                self.subject_box.addItem(subject_name)  # timer tab
                self.subject_dropdown.addItem(subject_name)  # add tab

                self.subject_box.setCurrentText(subject_name)
                self.subject_dropdown.setCurrentText(subject_name)

                add_subject(subject_name)

    def _rm_session_type(self):
        reply = QMessageBox.question(
            self,
            "Removing Subject",
            f"Are you sure you want to delete '{self.subject_box.currentText()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            print("User confirmed")
            self.subjects.remove(self.subject_box.currentText())
            self.subject_box.removeItem(self.subject_box.currentIndex())

    def _session_list(self):
        return [self.subject_box.itemText(i) for i in range(self.subject_box.count())]

    def _start_work(self):
        if self.work_done and self.start_btn.text().lower().strip() == "▶ start break":
            self._start_break()
        else:
            self._start_session("work", self.work_slider.value())
            self.work_started_at = datetime.now()

    def _start_break(self):
        self._start_session("break", self.break_slider.value())

    def _start_session(self, kind, minutes):
        self.current_session = kind
        self.total_time = timedelta(minutes=minutes)
        self.session_end_time = datetime.now() + self.total_time
        self.remaining_time = self.total_time
        self.paused = False

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)

        self.work_slider.setEnabled(False)
        self.break_slider.setEnabled(False)
        self.subject_box.setEnabled(False)

        self._update_circle()
        self.timer.start(1000)

    def _stop_session(self):
        self._reset()

    def _pause_resume(self):
        if self.paused:
            self.session_end_time = datetime.now() + self.remaining_time
            self.timer.start(1000)
            self.pause_btn.setText("⏸ Pause")
        else:
            self.remaining_time = self.session_end_time - datetime.now()
            self.timer.stop()
            self.pause_btn.setText("▶ Resume")
        self.paused = not self.paused

    def _tick(self):
        self.remaining_time = self.session_end_time - datetime.now()
        if self.remaining_time.total_seconds() <= 0:
            self.timer.stop()
            self._session_done()
            return
        self._update_circle()

    def _update_circle(self):
        total_secs = int(self.remaining_time.total_seconds())
        mins, secs = divmod(total_secs, 60)
        percent = 1 - self.remaining_time / self.total_time
        self.circle.update_progress(percent, f"{mins:02}:{secs:02}")

    def _session_done(self):
        play_sound()
        self.tray.showMessage("Pomodoro", "Time's up!", QSystemTrayIcon.Information)

        if self.current_session == "work":
            self.work_done = True
            title = f"{self.subject_box.currentText()} Pomodoro"
            create_calendar_event(title, self.work_started_at, datetime.now())
            self.start_btn.setText("▶ Start Break")
        else:
            self.start_btn.setText("▶ Start Work")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.work_slider.setEnabled(True)
        self.break_slider.setEnabled(True)
        self.subject_box.setEnabled(True)

        self.current_session = None

    def closeEvent(self, ev):
        if (
            QMessageBox.question(
                self,
                "Quit",
                "Exit Pomodoro Timer?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self._questions_manager.save_questions()
            ev.accept()
        else:
            ev.ignore()
