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
import sys

import dotenv
import qdarktheme
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from src.gui.pomlet_window import PomletWindow
from sync.cloud import download, update

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print(dotenv.find_dotenv())
    load_dotenv()

    download()
    app = QApplication(sys.argv)
    window = PomletWindow()
    qdarktheme.setup_theme("auto")
    window.show()

    exit_code: int = app.exec()
    if exit_code == 0:
        update()
    sys.exit(exit_code)
