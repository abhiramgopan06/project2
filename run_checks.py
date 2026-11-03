"""Run the project's standard Django checks and tests.

Usage:
    python run_checks.py
"""
import os
import subprocess
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rental_platform.settings")

commands = [
    [sys.executable, "manage.py", "check"],
    [sys.executable, "manage.py", "test"],
]

for command in commands:
    result = subprocess.run(command)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
