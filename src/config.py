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

import json
import os
from pathlib import Path


def get_config_path() -> Path:
    print(os.getenv("DEV"))
    if os.getenv("DEV") == "True":
        return Path().joinpath("config.json")

    dir_: Path = Path.home().joinpath(".pomodoro")
    dir_.mkdir(exist_ok=True)
    return dir_.joinpath("config.json")


def load_config(subject: str | None):
    """Load the configuration file with saved slider values."""
    if not get_config_path().exists() or subject is None:
        return 25, 5

    config = _load_config()
    if config.get(subject) is None:
        return 25, 5

    return (
        config[subject].get("work_duration", 25),
        config[subject].get("break_duration", 5),
    )


def modify_subject(subject: str, work_duration: int, break_duration: int):
    if not get_config_path().exists() or subject is None:
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
    config_file: Path = get_config_path()
    if not config_file.exists():
        config_file.parent.mkdir(exist_ok=True)

    _write_config(config)


def add_subject(subject: str):
    config = _load_config()
    config[subject] = {
        "work_duration": 25,
        "break_duration": 5,
    }

    _write_config(config)


def remove_subject(subject: str):
    config = _load_config()
    if config.get(subject) is None:
        return

    config.pop(subject)
    _write_config(config)


def get_subjects():
    if not get_config_path().exists():
        return []
    config = _load_config()
    return list(config.keys())


def _write_config(config: dict):
    with open(get_config_path(), "w", encoding="utf-8") as f:
        json.dump(config, f)


def _load_config():
    config_file: Path = get_config_path()
    if not config_file.exists():
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)
