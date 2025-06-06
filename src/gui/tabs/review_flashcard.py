from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.questions_manager import QuestionManager


class ReviewTab(QWidget):
    def __init__(self, questions_manager: QuestionManager):
        super().__init__()

        self._questions_manager = questions_manager
        self._ok_btn: QPushButton = QPushButton("✓ Correct") 
        self._wrong_btn: QPushButton = QPushButton("✗ Wrong")
        self._start_review_btn: QPushButton = QPushButton("▶ Start Review")
        self._current_question: Optional[Dict[str, Any]] = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        # Title label for the subject
        self.subject_label = QLabel()
        self.subject_label.setText("Course")
        self.subject_label.setWordWrap(True)
        self.subject_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subject_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            margin: 15px;
        """)

        # Flashcard count label
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setText(
            f"There are {self._questions_manager.count()} flashcards to review"
        )
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setStyleSheet("""
            font-size: 16px;
            margin: 10px;
        """)

        # Buttons layout (review controls)
        btns = QHBoxLayout()

        self.ok_btn.setEnabled(False)
        self.wrong_btn.setEnabled(False)

        self.ok_btn.clicked.connect(self._on_correct)
        self.start_review_btn.clicked.connect(self._on_start_review)
        self.wrong_btn.clicked.connect(self._on_wrong)

        btns.addWidget(self.ok_btn)
        btns.addWidget(self.start_review_btn)
        btns.addWidget(self.wrong_btn)

        layout.addWidget(self.subject_label)
        layout.addStretch()
        layout.addWidget(self.question_label)
        layout.addStretch()
        layout.addLayout(btns)

        shortcut_correct = QShortcut(QKeySequence("Left"), self)
        shortcut_incorrect = QShortcut(QKeySequence("Right"), self)
        shortcut_correct.activated.connect(
            lambda: None if not self.ok_btn.isEnabled() else self._on_correct()
        )
        shortcut_incorrect.activated.connect(
            lambda: None if not self.wrong_btn.isEnabled() else self._on_wrong()
        )

    def _end_review(self):
        self.question_label.setText("Done")
        self.ok_btn.setEnabled(False)
        self.wrong_btn.setEnabled(False)

    def _on_correct(self):
        if self._current_question is None:
            return
        
        self._questions_manager.correct(self._current_question)
        next_question: Dict[str, Any] | None = self._questions_manager.get_next_to_repeat()

        if next_question is None:
            self._end_review()
            return

        self.question_label.setText(next_question["question"])
        self.subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def _on_start_review(self):
        self.ok_btn.setEnabled(True)
        self.wrong_btn.setEnabled(True)
        self.start_review_btn.setEnabled(False)
        next_question: Dict[str, Any] | None = self._questions_manager.get_next_to_repeat()

        if next_question is None:
            self._end_review()
            return

        self.question_label.setText(next_question["question"])
        self.subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def _on_wrong(self):
        if self._current_question is None:
            return
        
        self._questions_manager.wrong(self._current_question)
        next_question: Dict[str, Any] | None = self._questions_manager.get_next_to_repeat()

        if next_question is None:
            self._end_review()
            return

        self.question_label.setText(next_question["question"])
        self.subject_label.setText(next_question["subject"])
        self._current_question = next_question

    def on_flashcard_added(self):
        self.question_label.setText(
            f"There are {self._questions_manager.count()} flashcards to review"
        )

    @property
    def start_review_btn(self):
        return self._start_review_btn

    @property
    def ok_btn(self):
        return self._ok_btn

    @property
    def wrong_btn(self):
        return self._wrong_btn
