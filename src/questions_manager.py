from copy import copy
import json
from pathlib import Path
import shutil
from datetime import datetime, timedelta
from random import shuffle
from typing import Any, Dict, List

from src.config import get_config_path


class QuestionManager:
    def __init__(self) -> None:
        self._questions = self._load_questions()
        self._questions_to_repeat = self._get_flashcards_to_repeat()

    def _get_question_path(self):
        return get_config_path().parent.joinpath("questions.json")
    
    def _load_questions(self):
        question_path: Path = self._get_question_path()
        if not question_path.exists():
            with open(question_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(question_path, encoding="utf-8") as f:
            return json.load(f)

    def save_questions(self):
        question_path: Path = self._get_question_path()

        backups_dir = question_path.parent.joinpath("backups")
        backups_dir.mkdir(exist_ok=True)
        shutil.copyfile(
            question_path,
            backups_dir.joinpath(datetime.now().isoformat()),
        )

        with open(question_path, "w", encoding="utf-8") as f:
            return json.dump(self._questions, f)

    def _get_flashcards_to_repeat(self):
        qs = []
        for q in self._questions:
            if (
                q["next_repeat"] is not None
                and datetime.fromisoformat(q["next_repeat"]) <= datetime.now()
            ):  # None already repeated enough
                qs.append(q)

        shuffle(qs)

        for q in qs:
            yield q

    def count(self):
        return len([x for x in self._get_flashcards_to_repeat()])

    def correct(self, question: Dict[str, Any]) -> None:
        stored_question = self.find_question(question)
        stored_question["last_repeated"] = datetime.now().isoformat()
        stored_question["repeated"] += 1
        next_repeat = self._get_next_repeat(
            stored_question["repeated"], stored_question["last_repeated"]
        )
        stored_question["next_repeat"] = (
            next_repeat.isoformat() if next_repeat is not None else next_repeat
        )
        
        self.save_questions()


    def modify(self, question: Dict[str, Any]) -> None:
        stored_question = self.find_question(question)
        stored_question["question"] = question["question"]
        self.save_questions()

    def _id(self):
        if len(self._questions) == 0:
            return 0
        return max([x["id"] for x in self._questions]) + 1

    def add_question(self, question_text: str, subject: str) -> Dict[str, Any] | None:
        now = datetime.now().isoformat()
        question = {
            "id": self._id(),
            "question": question_text,
            "last_repeated": now,
            "created": now,
            "repeated": 0,
            "subject": subject,
        }
        next_repeat = self._get_next_repeat(
            question["repeated"], question["last_repeated"]
        )

        if next_repeat is None:
            return None

        question["next_repeat"] = next_repeat.isoformat()
        self._questions.append(question)
        self.save_questions()

        # reset generator of questions to be repeated
        self.reset()

        return question

    def _get_next_repeat(self, times, last_repeated):
        match times:
            case 0:
                delta = timedelta(hours=0)
            case 1:
                delta = timedelta(hours=12)
            case 2:
                delta = timedelta(days=1)
            case 3:
                delta = timedelta(days=3)
            case 4:
                delta = timedelta(days=7)
            case 5:
                delta = timedelta(days=14)
            case 5:
                delta = timedelta(days=31)
            case _:
                return None

        return datetime.fromisoformat(last_repeated) + delta

    def wrong(self, question: Dict[str, Any]) -> None:
        stored_question = self.find_question(question)
        stored_question["last_repeated"] = datetime.now().isoformat()
        stored_question["repeated"] = 0
        stored_question["next_repeat"] = (datetime.now() + timedelta(hours=1)).isoformat()
        self.save_questions()

    def find_question(self, question: Dict[str, Any]):
        for stored_question in self._questions:
            if stored_question["id"] == question["id"]:
                return stored_question
        
        raise ValueError("Question not found")
            
    def get_next_to_repeat(self):
        return next(self._questions_to_repeat, None)

    def reset(self):
        self._questions_to_repeat = self._get_flashcards_to_repeat()

    def get_all_grouped_by_subject(self):
        grouped_questions: Dict[str, List[Dict[str, Any]]] = {}

        for question in self._questions:
            if question["subject"] not in grouped_questions:
                grouped_questions[question["subject"]] = []

            grouped_questions[question["subject"]].append(question)

        return grouped_questions

    def find_by_id(self, id: int):
        for question in self._questions:
            if question["id"] == id:
                return copy(question)
            
    def remove(self, question: Dict[str, Any]):
        question = self.find_question(question)
        if question is None:
            return
        
        self._questions.remove(question)
        self.save_questions()
            
    @property
    def questions_to_repeat(self):
        return self._questions_to_repeat