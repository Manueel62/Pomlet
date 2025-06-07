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

import platform
import subprocess


def create_calendar_event(title, start_time, end_time):
    """Add an event to Apple Calendar (macOS only)."""
    if platform.system() != "Darwin":
        return  # skip if not on macOS

    applescript = (
        f"""
    set theStartDate to (current date)
    set hours of theStartDate to {start_time.hour}
    set minutes of theStartDate to {start_time.minute}
    set seconds of theStartDate to {start_time.second}

    set theEndDate to (current date)
    set hours of theEndDate to {end_time.hour}
    set minutes of theEndDate to {end_time.minute}
    set seconds of theEndDate to {end_time.second}
    """
        + '''
    tell application "Calendar"
        tell calendar "Pomodoro"
            make new event with properties {summary: "'''
        + title
        + """", start date:theStartDate, end date:theEndDate}
        end tell
    end tell
    """
    )
    subprocess.run(["osascript", "-e", applescript])
