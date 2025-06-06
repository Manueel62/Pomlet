import time
import subprocess
from datetime import datetime, timedelta
import platform
import sys


def play_sound():
    """Play a sound when the timer ends (macOS/Windows compatible)."""
    if platform.system() == "Darwin":  # macOS
        subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
    elif platform.system() == "Windows":
        import winsound

        winsound.Beep(1000, 500)  # Frequency (Hz), Duration (ms)
    else:
        print("\a")  # Fallback: System beep


def create_calendar_event(title, start_time, end_time):
    """Add an event to Apple Calendar (macOS only)."""
    if platform.system() != "Darwin":
        return  # Skip if not on macOS

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


def wait_for_enter(prompt):
    """Wait for user to press Enter before continuing."""
    input(f"⏳ {prompt} Press Enter to start... ")


def countdown(duration):
    """Displays a live countdown timer in MM:SS format."""
    end_time = datetime.now() + timedelta(seconds=duration)

    while True:
        remaining_time = end_time - datetime.now()
        if remaining_time.total_seconds() <= 0:
            sys.stdout.write("\r00:00\n")  # Ensures final 00:00 display
            sys.stdout.flush()
            break

        minutes, seconds = divmod(int(remaining_time.total_seconds()), 60)
        sys.stdout.write(f"\r{minutes:02}:{seconds:02}")  # Overwrites previous output
        sys.stdout.flush()
        time.sleep(1)


def pomodoro_timer():
    """Pomodoro timer with live countdown."""
    while True:
        # Work session (25 minutes)
        input("Press Enter to START WORK (50 minutes)...")
        start_time = datetime.now()
        print(f"🚀 WORK: {start_time.strftime('%H:%M')} — Focus for 25 minutes!")

        countdown(50 * 60)
        play_sound()
        print("\n✅ Pomodoro done! Still studying until you press Enter.")
        input("Press Enter to START BREAK (10 minutes)...")
        print("Logging to Calendar.")
        create_calendar_event("Pomodoro", start_time, datetime.now())

        print(f"☕ BREAK: {datetime.now().strftime('%H:%M')} — Relax for 5 minutes!")

        countdown(10 * 60)  # 5 minutes
        play_sound()
        print("\n⏰ Break over!")


if __name__ == "__main__":
    try:
        pomodoro_timer()
    except KeyboardInterrupt:
        print("\n👋 Timer stopped.")
        sys.exit(0)
