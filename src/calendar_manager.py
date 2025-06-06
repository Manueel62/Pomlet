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
