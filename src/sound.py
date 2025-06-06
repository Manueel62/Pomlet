import platform
import subprocess


def play_sound():
    """Play a sound when the timer ends (macOS/Windows compatible)."""
    if platform.system() == "Darwin":  # macOS
        subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
    elif platform.system() == "Windows":
        raise RuntimeError("Windows not supported")
    else:
        print("\a")  # Fallback: System beep
