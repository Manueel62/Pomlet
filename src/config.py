import json
from pathlib import Path

CONFIG_FILE = Path.home().joinpath(".pomodoro").joinpath("config.json")


def load_config(subject: str | None):
    """Load the configuration file with saved slider values."""
    if not CONFIG_FILE.exists() or subject is None:
        return 25, 5

    config = _load_config()
    if config.get(subject) is None:
        return 25, 5

    return (
        config[subject].get("work_duration", 25),
        config[subject].get("break_duration", 5),
    )


def modify_subject(subject: str, work_duration: int, break_duration: int):
    if not CONFIG_FILE.exists() or subject is None:
        return

    config = _load_config()
    if config.get(subject) is None:
        return

    config[subject]["work_duration"] = work_duration
    config[subject]["break_duration"] = break_duration

    _write_config(config)


def save_config(work_duration, break_duration, session_types):
    """Save the slider values to a configuration file."""
    config = {
        "work_duration": work_duration,
        "break_duration": break_duration,
        "session_types": session_types,
    }
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(exist_ok=True)

    _write_config(config)


def add_subject(subject):
    config = _load_config()
    config[subject] = {
        "work_duration": 25,
        "break_duration": 5,
    }

    _write_config(config)


def get_subjects():
    if not CONFIG_FILE.exists():
        return []
    config = _load_config()
    return list(config.keys())


def _write_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)


def _load_config():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
