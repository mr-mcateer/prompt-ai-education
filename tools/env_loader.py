"""
Secure environment loader for all project scripts.
Loads secrets from .env file so they never appear in scripts or CLI history.

Usage:
    from tools.env_loader import get_env
    canvas_token = get_env("CANVAS_API_TOKEN")
    canvas_url = get_env("CANVAS_API_URL")
"""
import os
import sys
from pathlib import Path


def _find_env_file():
    """Walk up from CWD or script dir to find .env"""
    search = Path.cwd()
    for _ in range(5):
        env_path = search / ".env"
        if env_path.exists():
            return env_path
        search = search.parent
    return None


def _load_env():
    """Parse .env file into os.environ (no third-party deps)."""
    env_path = _find_env_file()
    if env_path is None:
        print("WARNING: No .env file found. Create one in the project root.", file=sys.stderr)
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


# Auto-load on import
_load_env()


def get_env(key, required=True):
    """Get an environment variable. Raises if required and missing."""
    val = os.environ.get(key)
    if required and (val is None or val.startswith("your_")):
        print(f"ERROR: {key} is not set. Update your .env file.", file=sys.stderr)
        sys.exit(1)
    return val
