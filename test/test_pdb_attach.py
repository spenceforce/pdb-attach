# -*- mode: python -*-
"""pdb-attach tests."""
from __future__ import unicode_literals

import io
import os
import signal

from context import pdb_attach, pdb_detach
from skip import skip_windows


def test_detach():
    """Test the debugger goes to the next line then detaches."""
    inp = io.StringIO("detach\n")
    with open(os.devnull, "w") as f:
        debugger = pdb_detach.PdbDetach(stdin=inp, stdout=f)
        debugger.set_trace()
        assert True  # If pdb quits this will never be reached.


def test_state_changes():
    """Test the state changes that happen in the debugger persist."""
    val = False
    inp = io.StringIO("val = True\ndetach\n")
    with open(os.devnull, "w") as f:
        debugger = pdb_detach.PdbDetach(stdin=inp, stdout=f)
        debugger.set_trace()
        assert val is True


def test_correct_detach_line():
    """Test line after set_trace is superceded after the debugger detaches."""
    val = False
    inp = io.StringIO("n\nval = True\ndetach\n")
    with open(os.devnull, "w") as f:
        debugger = pdb_detach.PdbDetach(stdin=inp, stdout=f)
        debugger.set_trace()
        val = False
        assert val is True


@skip_windows
def test_signal_set():
    """Test the signal handler is set and unset by listen and unlisten."""
    pdb_attach.listen(0)
    assert isinstance(signal.getsignal(signal.SIGUSR2), pdb_detach._Handler)
    pdb_attach.unlisten()
    assert not isinstance(signal.getsignal(signal.SIGUSR2), pdb_detach._Handler)


@skip_windows
def test_original_signal_restored():
    """Test the original signal is restored by unlisten."""
    pdb_attach.listen(0)
    cur_sig = signal.getsignal(signal.SIGUSR2)
    pdb_attach.unlisten()
    assert cur_sig.original_handler is signal.getsignal(signal.SIGUSR2)


def test_precmd_handler_runs():
    """Test attached precmd handler is executed.

    If it executes the value in val will change to True.
    """
    # Treat val as a box (list) instead of a variable to get around Pythons
    # scoping rules.
    val = [False]

    def precmd(line):
        val[0] = True
        return line

    inp = io.StringIO("detach\n")
    with open(os.devnull, "w") as f:
        debugger = pdb_detach.PdbDetach(stdin=inp, stdout=f)
        debugger.attach_precmd_handler(precmd)
        debugger.set_trace()
        assert val[0] is True
