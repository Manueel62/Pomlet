from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.questions_manager import QuestionManager


class ReviewTab(QWidget):
    def __init__(self, questions_manager: QuestionManager):
        super().__init__()

        self._questions_manager = questions_manager
        self._correct_btn: QPushButton = QPushButton("✓ Correct")
        self._wrong_btn: QPushButton = QPushButton("✗ Wrong")
        self._start_review_btn: QPushButton = QPushButton("▶ Start Review")
        self._stop_review_btn: QPushButton = QPushButton("⏹")
        self._current_question: Optional[Dict[str, Any]] = None

        self._modify_btn: QPushButton = QPushButton("✎ Modify")
        self._confirm_btn: QPushButton = QPushButton("✓ Confirm")
        self._subject_label = QLabel()
        self._question_label = QLabel()
        self._modify_question_field = QTextEdit()

        self._question_stack = QStackedWidget()
        self._modify_btns_stack = QStackedWidget()
        self._build()

    def _build(self):
        self._modify_question_field.setFixedSize(300, 100)
        self._modify_btn.setEnabled(False)

        layout = QVBoxLayout(self)

        # header layour: subject and modify/confirm buttons
        header_layout = QHBoxLayout()
        self._subject_label.setText("Course")
        self._subject_label.setWordWrap(True)
        self._subject_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subject_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            margin: 15px;
        """)

        self._modify_btn.clicked.connect(self._modify_flashcard)
        self._confirm_btn.clicked.connect(self._confirm_modify)

        self._modify_btns_stack.setFixedSize(100, 32)
        self._modify_btns_stack.addWidget(self._modify_btn)
        self._modify_btns_stack.addWidget(self._confirm_btn)

        header_layout.addWidget(self._subject_label)
        header_layout.addStretch()
        header_layout.addWidget(self._modify_btns_stack)

        # Question label: count or question text
        # form with the modification field the question stack
        self._question_label.setWordWrap(True)
        self._set_question_label()
        self._question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._question_label.setStyleSheet("""
            font-size: 16px;
            margin: 10px;
        """)

        self._question_stack.addWidget(self._question_label)
        self._question_stack.addWidget(self._modify_question_field)

        # Buttons layout (review controls)
        btns = QHBoxLayout()

        # initially disabled, must start review first
        self._correct_btn.setEnabled(False)
        self._start_review_btn.setEnabled(self._questions_manager.count() > 0)
        self._stop_review_btn.setEnabled(False)
        self._wrong_btn.setEnabled(False)

        self._correct_btn.clicked.connect(self._on_correct)
        self._start_review_btn.clicked.connect(self._on_start_review)
        self._wrong_btn.clicked.connect(self._on_wrong)
        self._stop_review_btn.clicked.connect(self._on_stop_review)

        btns.addWidget(self._correct_btn)
        btns.addWidget(self._start_review_btn)
        btns.addWidget(self._wrong_btn)
        btns.addWidget(self._stop_review_btn)

        # build final layout
        layout.addLayout(header_layout)
        layout.addStretch()
        layout.addWidget(self._question_stack)
        layout.addStretch()
        layout.addLayout(btns)

        # shortcuts
        shortcut_correct = QShortcut(QKeySequence("Left"), self)
        shortcut_incorrect = QShortcut(QKeySequence("Right"), self)
        shortcut_correct.activated.connect(
            lambda: None if not self._correct_btn.isEnabled() else self._on_correct()
        )
        shortcut_incorrect.activated.connect(
            lambda: None if not self._wrong_btn.isEnabled() else self._on_wrong()
        )

    def _on_stop_review(self):
        self._stop_review_btn.setEnabled(False)
        self._start_review_btn.setEnabled(self._questions_manager.count() > 0)
        self._end_review()

    def _modify_flashcard(self):
        if self._current_question is None:
            return

        self._correct_btn.setEnabled(False)
        self._wrong_btn.setEnabled(False)

        self._modify_btns_stack.setCurrentWidget(self._confirm_btn)
        self._question_stack.setCurrentWidget(self._modify_question_field)
        self._modify_question_field.setText(self._current_question["question"])

    def _confirm_modify(self):
        if self._current_question is None:
            return

        if self._modify_question_field.toPlainText().strip() == "":
            QMessageBox.warning(
                self,
                "Empty Question",
                "The question field cannot be empty.",
                QMessageBox.StandardButton.Ok,
            )
            return  # Exit the function early

        self._modify_btns_stack.setCurrentWidget(self._modify_btn)
        self._question_stack.setCurrentWidget(self._question_label)
        self._current_question["question"] = self._modify_question_field.toPlainText()
        self._questions_manager.modify(self._current_question)
        self._question_label.setText(self._current_question["question"])

        self._correct_btn.setEnabled(True)
        self._wrong_btn.setEnabled(True)

    def _set_question_label(self):
        count: int = self._questions_manager.count()
        self._question_label.setText(
            f"There are {count} flashcards to review"
            if count > 0
            else "All done for today!"
        )

    def _end_review(self):
        self._modify_btn.setEnabled(False)
        self._stop_review_btn.setEnabled(False)
        self._set_question_label()
        self._correct_btn.setEnabled(False)
        self._wrong_btn.setEnabled(False)

        # reset question manager generator
        self._questions_manager.reset()

    def _on_correct(self):
        if self._current_question is None:
            return

        self._questions_manager.correct(self._current_question)
        next_question: Dict[str, Any] | None = (
            self._questions_manager.get_next_to_repeat()
        )

        if next_question is None:
            self._end_review()
            return

        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def _on_start_review(self):
        self._modify_btn.setEnabled(True)
        self._correct_btn.setEnabled(True)
        self._wrong_btn.setEnabled(True)
        self._stop_review_btn.setEnabled(True)
        self._start_review_btn.setEnabled(False)

        next_question: Dict[str, Any] | None = (
            self._questions_manager.get_next_to_repeat()
        )

        if next_question is None:
            self._end_review()
            return

        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def _on_wrong(self):
        if self._current_question is None:
            return

        self._questions_manager.wrong(self._current_question)
        next_question: Dict[str, Any] | None = (
            self._questions_manager.get_next_to_repeat()
        )

        if next_question is None:
            self._end_review()
            return

        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def on_flashcard_added(self):
        self._start_review_btn.setEnabled(True)

        self._question_label.setText(
            f"There are {self._questions_manager.count()} flashcards to review"
        )

    @property
    def start_review_btn(self):
        return self._start_review_btn

    @property
    def correct_btn(self):
        return self._correct_btn

    @property
    def wrong_btn(self):
        return self._wrong_btn
