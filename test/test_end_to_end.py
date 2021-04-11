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


def infinite_loop():
    """Run an infinite loop."""
    keep_running = True

    while keep_running:
        pass


def run_function(func, commands):
    """Run the function in a separate process with `pdb-attach` and send it commands.

    Args
    ----
    func: A function to run in a separate process with `pdb-attach`.
    commands: A list of strings that will be entered as commands to `pdb-attach`.

    Return
    ------
    The output from `pdb-attach` as a tuple (stdout, stderr).
    """
    # Wrap function with pdb_attach listening.
    def _func(port, channel):
        pdb_attach.listen(port)
        channel.put(1)
        func()
        pdb_attach.unlisten()

    channel = Queue()
    # Get an unused port.
    port = find_unused_port()

    # Run an infinite loop with that port.
    p_serv = Process(target=_func, args=(port, channel))
    p_serv.start()

    # Wait for the server to signal it's ready to connect.
    channel.get()

    # Run pdb_attach as a module.
    p_client = subprocess.Popen(
        ["python", "-m", "pdb_attach", str(p_serv.pid), str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p_client.communicate("\n".join(commands).encode())

    # If the commands were executed by the debugger, then this will return.
    p_serv.join()

    return out, err


@skip_windows
def test_end_to_end():
    """Test client commands are honored.

    It should change the running value to False and detach.
    """
    commands = ["keep_running = False", "detach"]
    out, _ = run_function(infinite_loop, commands)
    # If this point is reached in execution, that means the infinite loop
    # was terminated by changing the value through the debugger.

    # Ensure the prompt is output to the client.
    assert len(out) > 0
    assert b"(Pdb)" in out


@skip_windows
def test_empty_input():
    """Test empty string doesn't throw error."""
    commands = ["", "keep_running = False", "detach"]
    out, _ = run_function(infinite_loop, commands)

    assert b"(Pdb)" in out
