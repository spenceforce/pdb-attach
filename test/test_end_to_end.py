# -*- mode: python -*-
"""pdb-attach end to end tests."""
from __future__ import unicode_literals

import io
import os
import socket
import subprocess
import test.support as support
from multiprocessing import Process

import pytest

from context import pdb_attach, pdb_detach


def infinite_loop(port):
    """A function that runs an infinite loop."""
    pdb_attach.listen(port)
    keep_running = True

    while keep_running:
        pass

    pdb_attach.unlisten()


@pytest.mark.timeout(10)
def test_end_to_end():
    """Test client commands are honored.

    It should change the running value to False and detach.
    """
    # Get an unused port.
    port = support.find_unused_port()

    # Run an infinite loop with that port.
    p_serv = Process(target=infinite_loop, args=(port,))
    p_serv.start()

    # Run pdb_attach as a module with the stdin pointing to the input file.
    p_client = subprocess.Popen(['python', '-m', 'pdb_attach', str(p_serv.pid), str(port)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)# input_file.open())
    out, err = p_client.communicate(b'n\nkeep_running = False\ndetach\n')
    if len(err) > 0:
        print(err)

    # If the commands were executed by the debugger, then this will return.
    p_serv.join()

    # Ensure the prompt is output to the client.
    assert len(out) > 0
    assert b'(Pdb)' in out

    # Clean up for good measure.
    p_client.kill()
