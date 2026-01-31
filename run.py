#!/usr/bin/env python3
"""Run the bot (orchestrator entrypoint)."""

import uvloop

uvloop.install()

from app.main_orchestrator import main

if __name__ == "__main__":
    main()
