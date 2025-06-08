from datetime import datetime, timedelta
from typing import Optional, Callable

from PySide6.QtCore import QObject, QTimer, Signal

from src.timer.session_type import SessionType

class PomletTimer(QObject):
    tick = Signal(float, int, int)
    # started = Signal(SessionType)
    ended = Signal(SessionType)
    # stopped = Signal()
    # paused = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._current_session_type: SessionType = SessionType.NONE
        self._total_time: timedelta = timedelta()
        self._remaining_time: timedelta = timedelta()
        self._session_end_time: Optional[datetime] = None
        self._paused: bool = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._on_session_done: Optional[Callable[[SessionType], None]] = None

    def start_session(self, session_type: SessionType, minutes: int):
        if self._session_end_time is not None:
            return  # Session already running

        self._current_session_type = session_type
        self._total_time = timedelta(minutes=minutes)
        self._remaining_time = self._total_time
        self._session_end_time = datetime.now() + self._total_time
        self._paused = False

        self._timer.start(1000)
        # self.started.emit(session_type)

    def stop(self):
        self._timer.stop()
        self.reset()
        # self.stopped.emit()

    def pause(self):
        if not self._paused and self._session_end_time is not None:
            self._remaining_time = self._session_end_time - datetime.now()
            self._timer.stop()
            self._paused = True
            # self.paused.emit()

    def resume(self):
        if self._paused:
            self._session_end_time = datetime.now() + self._remaining_time
            self._timer.start(1000)
            self._paused = False
            # self.paused.emit()

    def is_paused(self) -> bool:
        return self._paused

    def current_session_type(self) -> SessionType:
        return self._current_session_type

    def _tick(self):
        if self._session_end_time is None:
            return

        self._remaining_time = self._session_end_time - datetime.now()
        total_seconds = int(self._remaining_time.total_seconds())

        if total_seconds <= 0:
            self._timer.stop()
            self._handle_session_done()
            return
        
        percent = 1 - self._remaining_time / self._total_time
        mins, secs = divmod(total_seconds, 60)
        self.tick.emit(percent, mins, secs)

    def _handle_session_done(self):
        self.ended.emit(self._current_session_type)
        self.reset()

    def reset(self):
        self._current_session_type = SessionType.NONE
        self._total_time = timedelta()
        self._remaining_time = timedelta()
        self._session_end_time = None
        self._paused = False