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
from math import log
import os
import sys

import qdarktheme
from dotenv import load_dotenv
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.pomlet_window import PomletWindow
from src.config import get_config_path

logger = logging.getLogger(__name__)


def setup_logger():
    dev_mode = os.getenv("DEV", "").lower() == "true"
    log_path = get_config_path().parent.joinpath("pomlet.log")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(filename)-15s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=None if dev_mode else log_path,
        filemode="w",
    )

    logger.debug("Dev mode: %s, logs at: %s", dev_mode, log_path)

if __name__ == "__main__":
    load_dotenv()
    setup_logger()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))
    window = PomletWindow()
    qdarktheme.setup_theme("auto")
    window.show()
    sys.exit(app.exec())
