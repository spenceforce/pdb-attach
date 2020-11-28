# -*- mode: python -*-
"""pdb-attach tests."""
from __future__ import unicode_literals

import io
import os
import signal
import socket
import subprocess
import sys
import pytest
from contextlib import closing

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pdb_attach
import pdb_attach.pdb_detach as pdb_detach


@pytest.fixture()
def free_port():
    """Return port number of a free port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def test_detach():
    """Test the debugger goes to the next line then detaches."""
    inp = io.StringIO("detach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert True  # If pdb quits this will never be reached.


def test_state_changes():
    """Test the state changes that happen in the debugger persist."""
    val = False
    inp = io.StringIO("val = True\ndetach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert val is True


def test_correct_detach_line():
    """Test line after set_trace is not executed after the debugger detaches."""
    val = False
    inp = io.StringIO("n\nval = True\ndetach\n")
    debugger = pdb_detach.PdbDetach(stdin=inp)
    debugger.set_trace()
    val = False
    assert val is True


def test_signal_set():
    """Test the signal handler is set and unset by listen and unlisten."""
    pdb_attach.listen(0)
    assert signal.getsignal(pdb_detach._signal).func is pdb_detach._handler
    pdb_attach.unlisten()
    cur_sig = signal.getsignal(pdb_detach._signal)
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
    debugger = pdb_detach.PdbDetach(stdin=inp)
    debugger.attach_precmd_handler(precmd)
    debugger.set_trace()
    assert val[0] is True


def test_end_to_end(free_port):
    """End to end test(s)."""
    test_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'end_to_end.sh'))
    # GitHub Actions for Windows runners fails to find bash on PATH without `shell=True`.
    returncode = subprocess.call('bash {} {}'.format(test_script, free_port), shell=True)
    assert returncode == 0
