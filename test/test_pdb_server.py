# -*- mode: python -*-
"""PdbServer tests."""
from __future__ import unicode_literals

import io

from context import pdb_server


def test_stdin_stdout_ignored():
    """Test the IO handles are removed from the Pdb object."""
    io_in, io_out = io.StringIO(), io.StringIO()
    debugger = pdb_server.PdbServer(0, stdin=io_in, stdout=io_out)
    assert debugger.stdin is not io_in
    assert debugger.stdout is not io_out
