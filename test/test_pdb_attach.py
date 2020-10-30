# -*- mode: python -*-
"""pdb-attach tests."""
import io
import os
import signal
import socket
import socketserver
import subprocess
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pdb_attach  # pylint: disable=wrong-import-position


@pytest.fixture
def free_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        free_port = s.server_address[1]
    return free_port


def test_detach():
    """Test the debugger goes to the next line then detaches."""
    inp = io.StringIO("detach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert True  # If pdb quits this will never be reached.


def test_state_changes():
    """Test the state changes that happen in the debugger persist."""
    val = False
    inp = io.StringIO("val = True\ndetach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert val is True


def test_correct_detach_line():
    """Test that the line after set_trace is not executed once by the debugger
    and again after the debugger exits.
    """
    val = False
    inp = io.StringIO("n\nval = True\ndetach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    val = False
    assert val is True


def test_signal_set():
    """Test the signal handler is set and unset by listen and unlisten."""
    pdb_attach.listen(0)
    assert signal.getsignal(signal.SIGUSR2).func is pdb_attach._handler
    pdb_attach.unlisten()
    cur_sig = signal.getsignal(signal.SIGUSR2)
    if hasattr(cur_sig, "func"):
        assert cur_sig.func is not pdb_attach._handler
    else:
        assert cur_sig is not pdb_attach._handler


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
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.attach_precmd_handler(precmd)
    debugger.set_trace()
    assert val[0] is True


def test_end_to_end(free_port):
    proc = subprocess.run("bash ./test/end_to_end.sh {}".format(free_port), shell=True)
    assert proc.returncode == 0
