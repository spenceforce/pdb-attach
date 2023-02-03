# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import os
import platform

from pdb_attach.pdb_signal import PdbSignal
from pdb_attach.pdb_select import PdbSelect

__all__ = ["listen", "unlisten"]

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION.txt")) as f:
    __version__ = f.read().strip()

if platform.system() == "Windows":
    def listen(port):
        """Start listening on port."""
        PdbSelect.listen(port)

    def unlisten():
        """Stop listening."""
        PdbSelect.unlisten()

else:
    def listen(port):
        """Start listening on port."""
        PdbSignal.listen(port)

    def unlisten():
        """Stop listening."""
        PdbSignal.unlisten()
