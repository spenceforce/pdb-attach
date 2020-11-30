# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import os

from .pdb_detach import listen, unlisten

__all__ = ["listen", "unlisten"]

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION.txt")) as f:
    __version__ = f.read().strip()
