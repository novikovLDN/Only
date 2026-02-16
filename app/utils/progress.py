"""Progress bar utility."""


def build_progress_bar(current_xp: int, required_xp: int) -> str:
    """Build 10-segment level progress bar. Returns e.g. '🟩🟩🟩⬜️⬜️⬜️⬜️⬜️⬜️⬜️ 30%'."""
    if required_xp == 0:
        return "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%"
    percent = int((current_xp / required_xp) * 100)
    percent = max(0, min(percent, 100))
    total_blocks = 10
    filled_blocks = int(percent / 10)
    bar = "🟩" * filled_blocks + "⬜️" * (total_blocks - filled_blocks)
    return f"{bar} {percent}%"
