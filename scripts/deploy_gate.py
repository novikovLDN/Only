#!/usr/bin/env python3
"""
Deployment gate — fail deploy if migrations not at head.

1. Run alembic upgrade head
2. Verify alembic current == alembic heads
If mismatch → FAIL DEPLOY HARD. Application MUST NOT start with outdated schema.
"""

import re
import subprocess
import sys


def _run(cmd: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout or "", r.stderr or ""


def _extract_revision(out: str) -> str | None:
    """Extract revision ID from '007 (head)' or '007' or 'abc123 (head)'."""
    out = out.strip()
    if not out:
        return None
    # First token is typically the revision
    match = re.match(r"([a-f0-9]+|[0-9]+)", out.split()[0] if out.split() else out)
    return match.group(1) if match else out.split()[0] if out.split() else None


def main() -> int:
    # 1. Apply migrations (use python -m for venv compatibility)
    code, out, err = _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    if code != 0:
        print("DEPLOY GATE FAILED: alembic upgrade head failed", file=sys.stderr)
        if err:
            print(err, file=sys.stderr)
        return 1

    # 2. Verify current == heads
    code_cur, out_cur, _ = _run([sys.executable, "-m", "alembic", "current"])
    code_heads, out_heads, _ = _run([sys.executable, "-m", "alembic", "heads"])

    if code_cur != 0 or code_heads != 0:
        print("DEPLOY GATE FAILED: could not read alembic state", file=sys.stderr)
        return 1

    current = _extract_revision(out_cur)
    # heads can have multiple lines if branching; take first
    first_head_line = (out_heads or "").strip().split("\n")[0]
    heads = _extract_revision(first_head_line)

    if not current or not heads:
        print("DEPLOY GATE FAILED: could not parse alembic current/heads", file=sys.stderr)
        return 1

    if current != heads:
        print(
            f"DEPLOY GATE FAILED: migrations mismatch. current={current!r} heads={heads!r}",
            file=sys.stderr,
        )
        return 1

    print("Deploy gate OK: schema at head")
    return 0


if __name__ == "__main__":
    sys.exit(main())
