import json
import shutil
from datetime import datetime, timedelta
from random import shuffle

from src.config import CONFIG_FILE

QUESTIONPATH = CONFIG_FILE.parent.joinpath("questions.json")


class QuestionManager:
    def __init__(self) -> None:
        self._questions = self._load_questions()
        self.questions_to_repeat = self.to_repeat()
        self.current_idx = None

    def _load_questions(self):
        if not QUESTIONPATH.exists():
            with open(QUESTIONPATH, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(QUESTIONPATH, encoding="utf-8") as f:
            return json.load(f)

    def save_questions(self):
        backups_dir = QUESTIONPATH.parent.joinpath("backups")
        backups_dir.mkdir(exist_ok=True)
        shutil.copyfile(QUESTIONPATH, backups_dir.joinpath(datetime.now().isoformat()))

        with open(QUESTIONPATH, "w", encoding="utf-8") as f:
            return json.dump(self._questions, f)

    def get_subject(self):
        if self.current_idx is None:
            return ""
        return self.questions_to_repeat[self.current_idx]["subject"]

    def to_repeat(self):
        qs = []
        for q in self._questions:
            if (
                q["next_repeat"] is not None
                and datetime.fromisoformat(q["next_repeat"]) <= datetime.now()
            ):  # None already repeated enough
                qs.append(q)

        shuffle(qs)
        return qs

    def count(self):
        return len([x for x in self.to_repeat()])

    def correct(self):
        if self.current_idx is None:
            raise ValueError

        for q in self._questions:
            if q["id"] == self.questions_to_repeat[self.current_idx]["id"]:
                q["last_repeated"] = datetime.now().isoformat()
                q["repeated"] += 1
                next_repeat = self._get_next_repeat(q["repeated"], q["last_repeated"])
                q["next_repeat"] = (
                    next_repeat.isoformat() if next_repeat is not None else next_repeat
                )

    def _id(self):
        if len(self._questions) == 0:
            return 0
        return max([x["id"] for x in self._questions]) + 1

    def add_question(self, question, subject):
        now = datetime.now().isoformat()
        question = {
            "id": self._id(),
            "question": question,
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

    def wrong(self):
        if self.current_idx is None:
            raise ValueError

        for q in self._questions:
            if q["id"] == self.questions_to_repeat[self.current_idx]["id"]:
                q["last_repeated"] = datetime.now().isoformat()
                q["repeated"] = 0
                q["next_repeat"] = datetime.now().isoformat()

    def get_next_to_repeat(self):
        if self.current_idx is None:
            self.current_idx = 0
        elif self.current_idx < len(self.questions_to_repeat):
            self.current_idx += 1

        if self.current_idx >= len(self.questions_to_repeat):
            return None

        return self.questions_to_repeat[self.current_idx]
