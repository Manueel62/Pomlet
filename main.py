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