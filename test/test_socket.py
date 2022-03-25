# -*- mode: python -*-
"""PdbServer tests."""
from __future__ import unicode_literals

import errno
import io
import os
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

from context import pdb_socket, PROMPT
from skip import skip_windows


CLOSED = "closed"
CONNECTED = "connected"
LISTENING = "listening"
SERV_RECEIVED = "received"
SERV_SENT = "sent"
CHANNEL_OUTPUTS = [CLOSED, CONNECTED, LISTENING, SERV_RECEIVED, SERV_SENT]


def test_pdbstr_is_prompt():
    data = "hello world"
    s = pdb_socket.PdbStr(data, True)
    assert s == data
    assert s.is_prompt


def test_pdbstr_is_not_prompt():
    data = "hello world"
    s = pdb_socket.PdbStr(data)
    assert s == data
    assert not s.is_prompt


def test_wrapper_properties():
    sock, _ = socket.socketpair()
    sock_io = sock.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    assert pdb_io.encoding == sock_io.encoding
    assert pdb_io.errors == sock_io.errors
    assert pdb_io.newlines == pdb_io.newlines


def test_wrapper_detach():
    sock, _ = socket.socketpair()
    sock_io = sock.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    assert pdb_io.buffer is sock_io.buffer
    pdb_io.detach()
    assert pdb_io.buffer is None and sock_io.buffer is None


def test_wrapper_read():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.read(len(msg)) == msg


def test_wrapper_read_one():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.read(1) == msg[0]


def test_wrapper_read_chunks():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.read(len(msg) - 2) == msg[:-2]
    assert pdb_io.read(2) == msg[-2:]


def test_wrapper_read_eof():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    sock2.close()
    assert pdb_io.read() == msg


def test_wrapper_readline():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world\n"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.readline() == msg


def test_wrapper_readline_newline_before_size():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world\n"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.readline(len(msg) + 1) == msg


def test_wrapper_readline_one():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world\n"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    assert pdb_io.readline(1) == msg[0]


def test_wrapper_readline_eof():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    sock2.send("{}|{}".format(len(msg), msg).encode())
    sock2.close()
    assert pdb_io.readline() == msg


def test_wrapper_write():
    sock1, sock2 = socket.socketpair()
    sock_io = sock1.makefile("rw")
    sock2 = sock2.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock_io)
    msg = "hello world"
    expected_msg = "{}|{}".format(len(msg), msg)
    assert pdb_io.write(msg) == len(msg)
    pdb_io.flush()
    assert sock2.read(len(expected_msg)) == expected_msg


def test_stdin_stdout_ignored():
    """Test the IO handles are removed from the Pdb object."""
    io_in, io_out = io.StringIO(), io.StringIO()
    debugger = pdb_socket.PdbServer(0, stdin=io_in, stdout=io_out)
    assert debugger.stdin is not io_in
    assert debugger.stdout is not io_out


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
            sock_io.write(pdb_socket.PdbIOWrapper._format_msg(output))
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

    client = pdb_socket.PdbClient(proc.pid, port)
    client.connect()

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

    client = pdb_socket.PdbClient(proc.pid, port)
    client.connect()

    command = "command"
    client.send_cmd(command)

    try:
        assert channels[SERV_RECEIVED].get(timeout=5) == pdb_socket.PdbIOWrapper._format_msg(command + os.linesep)
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

    client = pdb_socket.PdbClient(proc.pid, port)
    client.connect()

    # Wait for the server to close the connection.
    channels[CLOSED].get()

    _, closed = client.recv()
    assert closed is True
