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
from datetime import datetime

import requests
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config import get_subjects
from src.questions_manager import QuestionManager

logger = logging.getLogger(__name__)


class AddTab(QWidget):
    flashcard_added: Signal = Signal()

    def __init__(self, questions_manager: QuestionManager):
        super().__init__()
        self._questions_manager = questions_manager
        self._subject_box: QComboBox = QComboBox()
        self._add_flashcard_btn = QPushButton("Add Flashcard")
        self._question_input = QTextEdit()

        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        self._subject_box.addItems(get_subjects())

        self._add_flashcard_btn.setToolTip("Add a new flashcard")
        self._add_flashcard_btn.clicked.connect(self._on_add_flashcard_clicked)

        self._question_input.setFixedHeight(100)
        self._add_info_label: QLabel = QLabel("")

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_add_flashcard_clicked)

        layout.addWidget(self._subject_box)
        layout.addWidget(self._question_input)
        layout.addStretch()
        layout.addWidget(self._add_info_label)
        layout.addStretch()
        layout.addWidget(self._add_flashcard_btn)

        # now = datetime.now().isoformat()
        # question = {
        #     "id": self._id(),
        #     "question": question_text,
        #     "last_repeated": now,
        #     "created": now,
        #     "repeated": 0,
        #     "subject": subject,
        # }
        # next_repeat = self._get_next_repeat(
        #     question["repeated"], question["last_repeated"]
        # )

        # if next_repeat is None:
        #     return None

        # question["next_repeat"] = next_repeat.isoformat()
        # # self._questions.append(question)
        # # self.save_questions()

    def _on_add_flashcard_clicked(self):
        if self._question_input.toPlainText().strip() == "":
            return

        now = datetime.now().timestamp() * 1000
        question = {
            "question": self._question_input.toPlainText(),
            "course": self._subject_box.currentText(),
            "chapter": "BA",
            "lastRepeated": now,
            "timesRepeated": 0,
            "nextRepeat": now,
        }

        request = requests.post(
            f"http://{os.getenv('URL')}:{os.getenv('PORT')}/flashcards", json=question
        )

        print(request)
        if request.status_code != 201:
            logger.warning("Error while creating flashcard")
            return

        self._add_info_label.setText(
            f"""
            <div align="center">
                <h3>Question added!</h3>
                <p><b>Question:</b> {question["question"]}</p>
                <p><b>Subject:</b> {question["course"]}</p>
                <p><b>Chapter:</b> {question["chapter"]}</p>
            </div>
            """
        )
        self._question_input.setText("")

        # update count in review
        self.flashcard_added.emit()

    def on_subjects_updated(self, subject: str):
        logger.debug("Subject updated received in AddTab for: %s", subject)
        self._subject_box.clear()
        self._subject_box.addItems(get_subjects())

        if subject is None:  # subject deleted (no string passed)
            logger.debug("No subject given. Not setting current text.")
            return

        self._subject_box.setCurrentText(subject)

    @property
    def subject_dropdown(self):
        return self._subject_box

    @property
    def add_flashcard_btn(self):
        return self._add_flashcard_btn

    @property
    def question_input(self):
        return self._question_input

    @property
    def add_info_label(self):
        return self._add_info_label

    @property
    def questions_manager(self):
        return self._questions_manager
