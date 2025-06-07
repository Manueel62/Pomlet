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

from datetime import datetime
from typing import Any, Dict, Optional
from venv import logger

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.questions_manager import QuestionManager


class ListTab(QWidget):
    def __init__(self, questions_manager: QuestionManager):
        super().__init__()
        self._questions_manager = questions_manager

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Question", "#", "Next (days)", "ID"])
        self._id_index = 3
        self._tree.setColumnCount(4)
        self._tree.setColumnHidden(self._id_index, True)

        self._info_label = QLabel("All questions grouped by subject.")
        self._info_stacked_widget: Optional[QStackedWidget] = None
        self._modify_stacked_btn: Optional[QStackedWidget] = None
        self._modify_text_edit: Optional[QTextEdit] = None
        self._build()

    def _build(self):
        self._info_label.setStyleSheet("""
            QPushButton { 
                height: 50px;
                width: 100px;
            }

        """)
        layout = QVBoxLayout(self)
        layout.addWidget(self._info_label)
        layout.addWidget(self._tree)

        self._tree.itemDoubleClicked.connect(self._show_info)
        self.refresh()

    def _show_info(self, item: QTreeWidgetItem):
        if item.parent() is None:
            return

        question_id: int = int(item.text(self._id_index).strip())
        question = self._questions_manager.find_by_id(question_id)

        if question is None:
            return

        dialog = QDialog(self)
        dialog.setFixedSize(300, 500)
        dialog.setWindowTitle("Flashcard Info")
        layout = QVBoxLayout(dialog)

        def get_content(content: str):
            label_content = QLabel(content)
            label_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_content.setWordWrap(True)
            return label_content

        def add_section(title: str, content: QWidget):
            group = QVBoxLayout()
            label_title = QLabel(f"<b>{title}</b>")
            label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            group.addWidget(label_title)
            group.addWidget(content)

            frame = QFrame()
            frame.setLayout(group)
            frame.setFrameShape(QFrame.Shape.Box)
            layout.addWidget(frame)

        stack_widget = QStackedWidget()
        stack_widget.addWidget(get_content(question["question"]))
        self._modify_text_edit = QTextEdit(question["question"])
        stack_widget.addWidget(self._modify_text_edit)
        self._info_stacked_widget = stack_widget

        add_section("Question", stack_widget)

        add_section("Repetitions", get_content(str(question["repeated"])))
        add_section(
            "Last Repetition",
            get_content(
                datetime.fromisoformat(question["last_repeated"]).strftime(
                    "%Y-%m-%d %H:%M"
                )
            ),
        )
        add_section(
            "Next Repetition",
            get_content(
                datetime.fromisoformat(question["next_repeat"]).strftime(
                    "%Y-%m-%d %H:%M"
                )
            ),
        )

        # --- Buttons ---
        btn_modify = QPushButton("Modify")
        btn_save = QPushButton("Save")

        self._modify_stacked_btn = QStackedWidget()
        self._modify_stacked_btn.addWidget(btn_modify)
        self._modify_stacked_btn.addWidget(btn_save)
        self._modify_stacked_btn.setFixedHeight(30)

        button_layout = QHBoxLayout()
        btn_remove = QPushButton("Remove")
        btn_back = QPushButton("Back")

        button_layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addStretch()

        button_layout.addWidget(
            self._modify_stacked_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )
        button_layout.addWidget(btn_remove, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(button_layout)

        # --- Button Logic ---
        btn_back.clicked.connect(lambda: self._back(dialog))
        btn_remove.clicked.connect(lambda: self._on_remove_question(dialog, question))
        btn_modify.clicked.connect(self._on_modify_question)
        btn_save.clicked.connect(lambda: self._save_changes(dialog, question))

        dialog.exec()

    def _back(self, dialog: QDialog):
        if self._info_stacked_widget is None or self._modify_stacked_btn is None:
            return

        if self._info_stacked_widget.currentWidget() != self._modify_text_edit:
            self._close_dialog(dialog)
            return

        self._info_stacked_widget.setCurrentIndex(0)
        self._modify_stacked_btn.setCurrentIndex(0)

    def _close_dialog(self, dialog: QDialog):
        dialog.close()
        self.refresh()
        self._info_stacked_widget = None
        self._modify_stacked_btn = None
        self._modify_text_edit = None

    def _on_remove_question(self, dialog: QDialog, question: Dict[str, Any]):
        confirm = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to delete the flashcard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self._questions_manager.remove(question)
            self._close_dialog(dialog)

    def _on_modify_question(self):
        if (
            self._info_stacked_widget is None
            or self._modify_stacked_btn is None
            or self._modify_text_edit is None
        ):
            return

        self._info_stacked_widget.setCurrentWidget(self._modify_text_edit)
        self._modify_stacked_btn.setCurrentIndex(1)
        self._info_stacked_widget.currentWidget()

    def _save_changes(self, dialog: QDialog, question: Dict[str, Any]):
        if self._modify_text_edit is None:
            return

        question["question"] = self._modify_text_edit.toPlainText()
        self._questions_manager.modify(question)
        self._close_dialog(dialog)

    def refresh(self):
        """Rebuild the tree from current questions."""
        logger.debug("Refreshing ListTab tree...")

        self._tree.clear()
        grouped = self._questions_manager.get_all_grouped_by_subject()

        for subject, questions in grouped.items():
            subject_item = QTreeWidgetItem([subject])
            subject_item.setFirstColumnSpanned(True)

            self._tree.addTopLevelItem(subject_item)

            for question in questions:
                n_reps: str = str(question["repeated"])
                next_rep: str = str(
                    (
                        datetime.fromisoformat(question["next_repeat"]) - datetime.now()
                    ).days
                )
                question_item = QTreeWidgetItem(
                    [
                        question["question"].strip(),
                        n_reps.strip(),
                        next_rep.strip(),
                        str(question["id"]),
                    ]
                )
                subject_item.addChild(question_item)

        self._tree.expandAll()
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setMaximumSectionSize(200)
