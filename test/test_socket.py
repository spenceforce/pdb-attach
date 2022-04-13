# -*- mode: python -*-
"""PdbServer tests."""
from __future__ import unicode_literals

import io
import os
import socket

try:
    from test.support.socket_helper import find_unused_port
except ImportError:
    from test.support import find_unused_port

import pytest

from context import pdb_socket


def _server():
    port = find_unused_port()
    sock = socket.socket()
    sock.bind(("localhost", port))
    sock.listen(0)
    return (port, sock)


def _socketpair():
    """Fallback for missing `socket.socketpair`."""
    port, serv = _server()
    sock1 = socket.create_connection(("localhost", port))
    sock2, _ = serv.accept()
    return sock1, sock2


if not hasattr(socket, "socketpair"):
    socket.socketpair = _socketpair


@pytest.fixture()
def server():
    """Return a port and a socket server listening on that port."""
    return _server()


def test_pdbstr_is_prompt():
    """Test `_PdbStr` prompt is `True`."""
    data = "hello world"
    s = pdb_socket._PdbStr(data, True)
    assert s == data
    assert s.is_prompt


def test_pdbstr_is_not_prompt():
    """Test `_PdbStr` prompt is `False`."""
    data = "hello world"
    s = pdb_socket._PdbStr(data)
    assert s == data
    assert not s.is_prompt


def test_wrapper_read():
    """Test the IO wrappers `read` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.read(len(msg)) == msg


def test_wrapper_read_one():
    """Test the IO wrappers `read` method with a fixed size."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.read(1) == msg[0]


def test_wrapper_read_chunks():
    """Test the IO wrappers `read` method on chunks of data."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.read(len(msg) - 2) == msg[:-2]
    assert pdb_io.read(2) == msg[-2:]


def test_wrapper_read_eof():
    """Test the IO wrappers `read` method reads to EOF."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    sock2.close()
    assert pdb_io.read() == msg


def test_wrapper_readline():
    """Test the IO wrappers `readline` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world" + os.linesep
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.readline() == msg


def test_wrapper_readline_newline_before_size():
    """Test the IO wrappers `readline` method reads a newline first."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world" + os.linesep
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.readline(len(msg) + 1) == msg


def test_wrapper_readline_one():
    """Test the IO wrappers `readline` method with a fixed size."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world" + os.linesep
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    assert pdb_io.readline(1) == msg[0]


def test_wrapper_readline_eof():
    """Test the IO wrappers `readline` method reads to EOF."""
    sock1, sock2 = socket.socketpair()
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    sock2.send("{}|0|{}".format(len(msg), msg).encode())
    sock2.close()
    assert pdb_io.readline() == msg


def test_wrapper_write():
    """Test the IO wrappers `write` method."""
    sock1, sock2 = socket.socketpair()
    sock2 = sock2.makefile("rw")
    pdb_io = pdb_socket.PdbIOWrapper(sock1)
    msg = "hello world"
    expected_msg = "{}|0|{}".format(len(msg), msg)
    assert pdb_io.write(msg) == len(msg)
    assert sock2.read(len(expected_msg)) == expected_msg


def test_wrapper_read_prompt():
    """Test the IO wrappers `read_prompt` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    msg = pdb_socket._PdbStr("prompt", prompt=True)
    pdb_io1.write(msg)
    prompt, _ = pdb_io2.read_prompt()
    assert prompt == msg


def test_wrapper_read_prompt_eof():
    """Test the IO wrappers `read_prompt` method reads until EOF."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    msg = "hello world"
    pdb_io1.write(msg)
    sock1.close()
    prompt, closed = pdb_io2.read_prompt()
    assert prompt == msg
    assert closed is True


def test_wrapper_raises_eoferror():
    """Test the IO wrappers `raise_eoferror` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    pdb_io1.raise_eoferror()
    with pytest.raises(EOFError):
        pdb_io2.read()


def test_stdin_stdout_ignored():
    """Test the IO handles are removed from the Pdb object."""
    io_in, io_out = io.StringIO(), io.StringIO()
    debugger = pdb_socket.PdbServer(0, stdin=io_in, stdout=io_out)
    assert debugger.stdin is not io_in
    assert debugger.stdout is not io_out


def test_send(server):
    """Test client sends commands properly."""
    port, serv = server
    client = pdb_socket.PdbClient(port)
    client.connect()
    sock, _ = serv.accept()
    serv_io = pdb_socket.PdbIOWrapper(sock)
    msg = "hello world"
    client.send(msg)
    assert serv_io.readline() == msg + os.linesep
    msg = "hellow world" + os.linesep
    client.send(msg)
    assert serv_io.readline() == msg


def test_recv(server):
    """Test client receives output properly."""
    port, serv = server
    client = pdb_socket.PdbClient(port)
    client.connect()
    sock, _ = serv.accept()
    serv_io = pdb_socket.PdbIOWrapper(sock)
    msg = "hello world" + os.linesep
    serv_io.write(msg)
    prompt = pdb_socket._PdbStr("prompt", prompt=True)
    serv_io.write(prompt)
    recv_msg, closed = client.recv()
    assert recv_msg == msg + prompt
    assert not closed


def test_recv_closed(server):
    """Test client returns `True` when the connection is closed."""
    port, serv = server
    client = pdb_socket.PdbClient(port)
    client.connect()
    sock, _ = serv.accept()

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    _, closed = client.recv()
    assert closed is True


def test_interact_write():
    """Test the interactive consoles `write` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    interact = pdb_socket.PdbInteractiveConsole(pdb_io1)
    msg = "hello world"
    interact.write(msg)
    assert pdb_io2.read(len(msg)) == msg


def test_interact_raw_input():
    """Test the interactive consoles `raw_input` method."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    interact = pdb_socket.PdbInteractiveConsole(pdb_io1)
    msg = "hello world" + os.linesep
    prompt = ">>> "
    pdb_io2.write(msg)
    assert interact.raw_input(prompt) == msg
    assert pdb_io2.read_prompt() == (prompt, False)


def test_interact_eoferror():
    """Test the interactive consoles raises `EOFError` when one is sent through the socket."""
    sock1, sock2 = socket.socketpair()
    pdb_io1 = pdb_socket.PdbIOWrapper(sock1)
    pdb_io2 = pdb_socket.PdbIOWrapper(sock2)
    interact = pdb_socket.PdbInteractiveConsole(pdb_io1)
    pdb_io2.raise_eoferror()
    with pytest.raises(EOFError):
        interact.raw_input()
