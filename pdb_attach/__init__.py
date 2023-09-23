# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import os
import platform
import warnings

from pdb_attach.pdb_signal import PdbSignal

__all__ = ["listen", "unlisten"]

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION.txt")) as f:
    __version__ = f.read().strip()

if platform.system() == "Windows":
    warnings.warn(
        (
            "pdb-attach does not support Windows. listen() does nothing and the "
            "pdb-attach client will not be able to attach to this process."
        ),
        UserWarning,
        stacklevel=1,
    )


def listen(port):
    """Start listening on port."""
    PdbSignal.listen(port)


def unlisten():
    """Stop listening."""
    PdbSignal.unlisten()
