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

import sys
from dotenv import load_dotenv

from PySide6.QtWidgets import QApplication
import dotenv
import qdarktheme
from src.gui.pomodoro import PomodoroApp



if __name__ == "__main__":
    print(dotenv.find_dotenv())
    load_dotenv()
    app = QApplication(sys.argv)
    window = PomodoroApp()
    qdarktheme.setup_theme("auto")
    window.show()
    sys.exit(app.exec())