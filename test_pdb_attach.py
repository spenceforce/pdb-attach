# -*- mode: python -*-
"""pdb-attach tests."""
import io
import os
import sys
import pytest  # pylint: disable=unused-import

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import pdb_attach  # pylint: disable=wrong-import-position


def test_detach():
    """Test the debugger goes to the next line then detaches."""
    inp = io.StringIO("detach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert True  # If pdb quits this will never be reached.


def test_state_changes():
    """Test the state changes that happen in the debugger persist."""
    val = 0
    inp = io.StringIO("val = 1\ndetach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    assert val == 1


def test_correct_detach_line():
    """Test that the line after set_trace is not executed once by the debugger
    and again after the debugger exits.
    """
    val = 0
    inp = io.StringIO("n\nval = 1\ndetach\n")
    debugger = pdb_attach.PdbDetach(stdin=inp)
    debugger.set_trace()
    val = 2
    assert val == 1
