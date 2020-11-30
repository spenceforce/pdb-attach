# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
from .pdb_detach import listen, unlisten

__all__ = ["listen", "unlisten"]

with open("VERSION.txt") as f:
    __version__ = f.read().strip()
