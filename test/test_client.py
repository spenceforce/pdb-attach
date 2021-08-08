# -*- mode: python -*-
"""pdb-attach tests for client API."""
from __future__ import unicode_literals

import errno
import signal
import socket
from multiprocessing import Process, Queue

try:
    import queue
except ImportError:
    import Queue as queue

try:
    from test.support.socket_helper import find_unused_port
except ImportError:
    from test.support import find_unused_port

import pytest

from context import pdb_client, PROMPT
from skip import skip_windows

CLOSED = "closed"
CONNECTED = "connected"
LISTENING = "listening"
SERV_RECEIVED = "received"
SERV_SENT = "sent"
SIGNAL = "signal"
CHANNEL_OUTPUTS = [CLOSED, CONNECTED, LISTENING, SERV_RECEIVED, SERV_SENT, SIGNAL]


def run_server(close_on_connect=False):
    """Run a simple socket server.

    Parameters
    ----------
    close_on_connect
        Close the connection immediately after it's been established.

    Returns
    -------
    multiprocess.Process
        Process running the server.
    int
        Port of the server.
    dict
        Mapping from channel outputs to the corresponding channels those outputs
        will be sent through.

    Notes
    -----
    It is the callers responsibility to kill the process.
    """

    def _run_server(port, channels, close_on_connect=False):
        # Ignore SIGUSR2.
        signal.signal(
            signal.SIGUSR2, lambda signum, frame: channels[SIGNAL].put(SIGNAL)
        )

        # Set up server.
        sock = socket.socket()
        sock.bind(("localhost", port))
        sock.listen(1)
        channels[LISTENING].put(LISTENING)

        # Wait for connection.
        while True:
            try:
                serv, _ = sock.accept()
            except socket.error as e:
                if e.errno != errno.EINTR:
                    raise
            else:
                break
        channels[CONNECTED].put(CONNECTED)

        if close_on_connect is True:
            # This is mainly to test how the client responds to a closed
            # connection.
            serv.close()
            channels[CLOSED].put(CLOSED)
            return

        try:
            sock_io = serv.makefile("rw", buffering=1)
        except TypeError:
            # Unexpected keyword argument. Try bufsize.
            sock_io = serv.makefile("rw", bufsize=1)

        line = ""
        msg = 0
        while line not in ["quit", "q"]:
            output = "Message {}\n{}".format(msg, PROMPT)
            sock_io.write(output)
            channels[SERV_SENT].put(output)
            msg += 1

            line = sock_io.readline()
            channels[SERV_RECEIVED].put(line)

    channels = {out: Queue() for out in CHANNEL_OUTPUTS}
    port = find_unused_port()
    p_serv = Process(target=_run_server, args=(port, channels, close_on_connect))
    p_serv.start()

    # Ensure server is listening.
    channels[LISTENING].get()

    return (p_serv, port, channels)


@skip_windows
def test_connect():
    """Test client sends signal and connects to server."""
    proc, port, channels = run_server()

    client = pdb_client.PdbClient(proc.pid, port)
    client.connect()

    try:
        assert channels[SIGNAL].get(timeout=5) == SIGNAL
    except queue.Empty:
        proc.terminate()
        pytest.fail("Signal was not sent to server.")
    try:
        assert channels[CONNECTED].get(timeout=5) == CONNECTED
    except queue.Empty:
        proc.terminate()
        pytest.fail("Failed to connect to the server.")

    proc.terminate()


@skip_windows
def test_send_cmd_and_recv():
    """Test client sends commands properly."""
    proc, port, channels = run_server()

    client = pdb_client.PdbClient(proc.pid, port)
    client.connect()

    command = "command"
    client.send_cmd(command)

    try:
        assert channels[SERV_RECEIVED].get(timeout=5).strip() == command
    except queue.Empty:
        proc.terminate()
        pytest.fail("Server did not receive command.")

    from_server, closed = client.recv()
    try:
        assert channels[SERV_SENT].get(timeout=5) == from_server
    except queue.Empty:
        proc.terminate()
        pytest.fail("Server did not send output.")

    assert closed is False

    proc.terminate()


@skip_windows
def test_recv_closed():
    """Test client returns `True` when the connectin is closed."""
    proc, port, channels = run_server(close_on_connect=True)

    client = pdb_client.PdbClient(proc.pid, port)
    client.connect()

    # Wait for the server to close the connection.
    channels[CLOSED].get()

    _, closed = client.recv()
    assert closed is True
