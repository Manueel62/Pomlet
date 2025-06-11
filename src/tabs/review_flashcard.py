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
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from PySide6.QtCore import Qt, Signal
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

logger = logging.getLogger(__name__)


class ReviewTab(QWidget):
    flashcard_modified: Signal = Signal()

    def __init__(self):
        super().__init__()
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

    def question_to_review(self) -> Dict[str, Any]:
        if self._question_to_review is None:
            response = requests.get(
                f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards?review=true"
            )
            if response.status_code != 200:
                logger.error("Request failed with status code:", response.status_code)
                return {}

            self._question_to_review = response.json()

        return self._question_to_review

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
        self._start_review_btn.setEnabled(False)
        response = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/count"
        )
        print(response.text)
        self._start_review_btn.setEnabled(int(response.text) > 0)
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
        response = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/count"
        )

        if response.status_code != 200:
            logger.error("Request failed with status code:", response.status_code)
            return

        self._start_review_btn.setEnabled(int(response.text) > 0)
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

        response = requests.put(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/{self._current_question['id']}",
            json=self._current_question,
        )

        if response.status_code != 200:
            logger.error("Request failed with status code:", response.status_code)
            return

        # self._questions_manager.modify(self._current_question)
        self._question_label.setText(self._current_question["question"])

        self._correct_btn.setEnabled(True)
        self._wrong_btn.setEnabled(True)
        self.flashcard_modified.emit()

    def _set_question_label(self):
        # count: int = self._questions_manager.count()
        count = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/count"
        )

        if count.status_code != 200:
            logger.error("Request failed with status code:", count.status_code)
            return

        self._question_label.setText(
            f"There are {count.text} flashcards to review"
            if int(count.text) > 0
            else "All done for today!"
        )

    def _end_review(self):
        self._modify_btn.setEnabled(False)
        self._stop_review_btn.setEnabled(False)
        self._set_question_label()
        self._correct_btn.setEnabled(False)
        self._wrong_btn.setEnabled(False)

        # reset question manager generato
        self._question_to_review = None
        self._pointer = 0
        # self._questions_manager.reset()

    def _get_next_repeat(self, times, last_repeated):
        match times:
            case 0:
                delta = timedelta(hours=0)
            case 1:
                delta = timedelta(days=1)
            case 2:
                delta = timedelta(days=3)
            case 3:
                delta = timedelta(days=7)
            case 4:
                delta = timedelta(days=14)
            case 5:
                delta = timedelta(days=31)
            case _:
                return None

        return datetime.fromtimestamp(last_repeated/1000) + delta

    def correct(self, question: Dict[str, Any]) -> None:
        question["lastRepeated"] = int(datetime.now().timestamp() * 1000)
        question["timesRepeated"] += 1
        next_repeat = self._get_next_repeat(
            question["timesRepeated"], question["lastRepeated"]
        )
        question["nextRepeat"] = (
            int(next_repeat.timestamp()*1000) if next_repeat is not None else next_repeat
        )

        response = requests.put(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/{question['id']}",
            json=question,
        )

        if response.status_code != 200:
            logger.error("Request failed with status code:", response.status_code)
            return
        

    def _on_correct(self):
        if self._current_question is None:
            return

        self.correct(self._current_question)
        self.flashcard_modified.emit()

        request = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/next"
        )

        if request.status_code == 404:
            self._end_review()
            return
        
        elif request.status_code != 200:
            logger.error("Request failed with status code:", request.status_code)
            return

        print(request.json())
        next_question = request.json()
        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["course"])
        self._current_question = next_question


    def _on_start_review(self):
        self._modify_btn.setEnabled(True)
        self._correct_btn.setEnabled(True)
        self._wrong_btn.setEnabled(True)
        self._stop_review_btn.setEnabled(True)
        self._start_review_btn.setEnabled(False)

        request = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/next"
        )

        if request.status_code == 404:
            self._end_review()
            return
        
        elif request.status_code != 200:
            logger.error("Request failed with status code:", request.status_code)
            return

        print(request.json())
        next_question = request.json()
        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["course"])
        self._current_question = next_question

    def wrong(self, question: Dict[str, Any]) -> None:
        question["lastRepeated"] = datetime.now().timestamp() * 1000
        question["timesRepeated"] = 0
        question["nextRepeat"] = int(
            (datetime.now() + timedelta(hours=1)).timestamp() * 1000
        )

        response = requests.put(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/{question['id']}",
            json=question,
        )

        if response.status_code != 200:
            logger.error("Request failed with status code:", response.status_code)
            return

    def _on_wrong(self):
        if self._current_question is None:
            return

        self.wrong(self._current_question)
        self.flashcard_modified.emit()

        request = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/next"
        )

        if request.status_code == 404:
            self._end_review()
            return
        
        elif request.status_code != 200:
            logger.error("Request failed with status code:", request.status_code)
            return

        print(request.json())
        next_question = request.json()
        self._question_label.setText(next_question["question"])
        self._subject_label.setText(next_question["course"])
        self._current_question = next_question

    def on_flashcard_added(self):
        self._start_review_btn.setEnabled(True)
        count = requests.get(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards/count"
        )

        if count.status_code != 200:
            logger.error("Request failed with status code:", count.status_code)
            return

        self._question_label.setText(f"There are {count.text} flashcards to review")

    @property
    def start_review_btn(self):
        return self._start_review_btn

    @property
    def correct_btn(self):
        return self._correct_btn

    @property
    def wrong_btn(self):
        return self._wrong_btn
