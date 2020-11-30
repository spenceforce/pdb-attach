# -*- mode: python -*-
"""pdb-attach tests."""
from __future__ import unicode_literals

import io
import os
import signal
import socket
import subprocess

import pytest

from context import pdb_attach, pdb_detach


def test_detach():
    """Test the debugger goes to the next line then detaches."""
    inp = io.StringIO("detach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp, stdout=open(os.devnull, 'w'))
    debugger.set_trace()
    assert True  # If pdb quits this will never be reached.


def test_state_changes():
    """Test the state changes that happen in the debugger persist."""
    val = False
    inp = io.StringIO("val = True\ndetach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp, stdout=open(os.devnull, 'w'))
    debugger.set_trace()
    assert val is True


def test_correct_detach_line():
    """Test line after set_trace is not executed after the debugger detaches."""
    val = False
    inp = io.StringIO("n\nval = True\ndetach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp, stdout=open(os.devnull, 'w'))
    debugger.set_trace()
    val = False
    assert val is True


def test_signal_set():
    """Test the signal handler is set and unset by listen and unlisten."""
    pdb_attach.listen(0)
    assert signal.getsignal(signal.SIGUSR2).func is pdb_detach._handler
    pdb_attach.unlisten()
    cur_sig = signal.getsignal(signal.SIGUSR2)
    if hasattr(cur_sig, "func"):
        assert cur_sig.func is not pdb_detach._handler
    else:
        assert cur_sig is not pdb_detach._handler


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
    debugger = pdb_detach.PdbDetach(stdin=inp, stdout=open(os.devnull, 'w'))
    debugger.attach_precmd_handler(precmd)
    debugger.set_trace()
    assert val[0] is True
