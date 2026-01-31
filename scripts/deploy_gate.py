#!/usr/bin/env python3
"""
Deployment gate — fail deploy if migrations not applied.

Run before app start. Exits 1 if schema out of sync.
Broken schema must never reach PROD.
"""

import subprocess
import sys


def main() -> int:
    r = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print("DEPLOY GATE FAILED: alembic upgrade head failed", file=sys.stderr)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        return 1
    print("Deploy gate OK: migrations applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
