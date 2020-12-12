# -*- mode: python -*-
"""pdb-attach end to end tests."""
from __future__ import unicode_literals

import subprocess
from multiprocessing import Process, Queue

try:
    from test.support.socket_helper import find_unused_port
except ImportError:
    from test.support import find_unused_port

from context import pdb_attach
from skip import skip_windows


def infinite_loop(port, channel):
    """Run an infinite loop."""
    pdb_attach.listen(port)
    keep_running = True

    # Signal this process is listening
    channel.put(1)

    while keep_running:
        pass

    pdb_attach.unlisten()


@skip_windows
def test_end_to_end():
    """Test client commands are honored.

    It should change the running value to False and detach.
    """
    channel = Queue()
    # Get an unused port.
    port = find_unused_port()

    # Run an infinite loop with that port.
    p_serv = Process(target=infinite_loop, args=(port, channel))
    p_serv.start()

    # Wait for the server to signal it's ready to connect.
    channel.get()

    # Run pdb_attach as a module with the stdin pointing to the input file.
    p_client = subprocess.Popen(
        ["python", "-m", "pdb_attach", str(p_serv.pid), str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p_client.communicate(b"keep_running = False\ndetach\n")
    if len(err) > 0:
        print(err)

    # If the commands were executed by the debugger, then this will return.
    p_serv.join()

    # Ensure the prompt is output to the client.
    assert len(out) > 0
    assert b"(Pdb)" in out
