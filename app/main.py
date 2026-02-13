"""
DEPRECATED: Use run.py as the single entrypoint.

python run.py  # canonical
python -m app.main  # redirects to same flow — DO NOT use for production
"""

if __name__ == "__main__":
    import uvloop
    uvloop.install()
    from app.main_orchestrator import main
    main()
