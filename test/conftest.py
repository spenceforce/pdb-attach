# -*- mode: python -*-
"""pytest specific code."""
import platform


if platform.system() != "Windows":
    collect_ignore = ["test_windows_import.py"]
