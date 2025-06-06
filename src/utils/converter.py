from datetime import datetime
from pathlib import Path

import pandas as pd

from src.questions_manager import QuestionManager
converted_data = []
qm = QuestionManager()

id_ = qm._id()

for data_path in Path("data").glob("*"):
    data = pd.read_csv(data_path, names=["question", "_"])["question"]
    now = datetime.now().isoformat()

    for question_block in data:
        question = {
            "id": id_,
            "question": question_block,
            "created": now,
            "last_repeated": now,
            "next_repeat": now,
            "repeated": 0,
            "subject": data_path.stem,
        }
        converted_data.append(question)
        id_ += 1

qm._questions = converted_data
qm.save_questions()