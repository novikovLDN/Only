"""Progress bar utility."""


def build_progress_bar(current_xp: int, required_xp: int) -> str:
    """Build 10-segment progress bar. Returns e.g. '███░░░░░░░ 30%'."""
    if required_xp == 0:
        return "██████████ 100%"
    percent = min(100, int((current_xp / required_xp) * 100))
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {percent}%"
