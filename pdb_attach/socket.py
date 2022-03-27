# -*- mode: python -*-
"""Debugger that uses sockets for I/O."""
import io
import os
import pdb
import socket

from pdb_attach._prompt import PROMPT


class _PdbStr(str):
    """Special string that indicates if it is a prompt."""

    def __new__(cls, value, prompt=False):
        self = str.__new__(cls, value)
        self._is_prompt = prompt
        return self

    @property
    def is_prompt(self):
        return self._is_prompt


class PdbIOWrapper(io.TextIOBase):
    """Wrapper for socket IO.

    Allows for smoother IPC. Data sent over socket is formatted `<msg_size>|<code>|<msg_text>`.
    """

    def __init__(self, sock):
        self._buffer = self._new_buffer()
        self._sock = sock
        try:
            self._io = self._sock.makefile("rw", buffering=1)
        except TypeError:
            # Unexpected keyword argument. Try bufsize.
            self._io = self._sock.makefile("rw", bufsize=1)  # type: ignore

    _TEXT = 0
    _PROMPT = 1
    _EOFERROR = 2

    @property
    def encoding(self):
        return self._io.encoding

    @property
    def errors(self):
        return self._io.errors

    @property
    def newlines(self):
        return self._io.newlines

    @property
    def buffer(self):
        return self._io.buffer

    @staticmethod
    def _format_msg(msg, code):
        return "{}|{}|{}".format(len(msg), code, msg)

    def _new_buffer(self):
        return ""

    def detach(self):
        self._buffer = None
        return self._io.detach()

    def _read(self):
        """Read from the socket."""
        msg_size = ""
        while True:
            msg_size += self._io.read(1)
            if len(msg_size) == 0:
                return _PdbStr("")

            if msg_size[-1] == "|":
                msg_size = int(msg_size[:-1])
                break
        code = self._io.read(2)
        code = int(code[:-1])
        msg = _PdbStr(self._io.read(msg_size), prompt=(code == 1))
        return msg

    def _read_eof(self):
        while True:
            prev_buf_size = len(self._buffer)
            self._buffer += self._read()
            if len(self._buffer) == prev_buf_size:
                break

    def read(self, size=-1):
        if size is None or size < 0:
            self._read_eof()
            rv, self._buffer = self._buffer, self._new_buffer()
            return rv

        while len(self._buffer) < size:
            self._buffer += self._read()

        rv, self._buffer = self._buffer[:size], self._buffer[size:]
        return rv

    def readline(self, size=-1):
        while os.linesep not in self._buffer:
            buf_size = len(self._buffer)
            if size >= 0 and buf_size >= size:
                break

            self._buffer += self._read()

            if len(self._buffer) == buf_size:
                break

        if size >= 0 and os.linesep in self._buffer:
            idx = min(size, self._buffer.index(os.linesep) + 1)
        elif size >= 0:
            idx = size
        elif os.linesep in self._buffer:
            idx = self._buffer.index(os.linesep) + 1
        else:
            idx = len(self._buffer)

        rv, self._buffer = self._buffer[:idx], self._buffer[idx:]
        return rv

    def read_prompt(self):
        """Read everything until a prompt is received and return it.

        Returns
        -------
        (str, bool) : A tuple containing the str output from the connection and
            a bool indicating if the connection is closed.
        """
        closed = False
        while True:
            msg = self._read()
            self._buffer += msg
            if len(msg) == 0 or msg.is_prompt:
                break

        rv, self._buffer = self._buffer, self._new_buffer()
        return rv, len(msg) == 0

    def write(self, msg):
        if not isinstance(msg, _PdbStr):
            msg = _PdbStr(msg)
        msg = self._format_msg(msg, code=(1 if msg.is_prompt else 0))
        write_n = self._io.write(msg)
        # Offset num bytes written by the additional characters in the formatted
        # message.
        return write_n - len(msg[: msg.index("|") + 3])

    def flush(self):
        return self._io.flush()


class PdbServer(pdb.Pdb):
    """PdbServer extends Pdb for communication via sockets."""

    # Set use_rawinput to False to defer io to file object arguments passed to
    # stdin and stdout.
    use_rawinput = False

    def __init__(self, port, *args, **kwargs):
        self._sock = socket.socket()
        self._sock.bind(("localhost", port))
        self._sock.listen(1)

        if "stdin" in kwargs:
            del kwargs["stdin"]
        if "stdout" in kwargs:
            del kwargs["stdout"]

        pdb.Pdb.__init__(self, *args, **kwargs)
        self.prompt = _PdbStr(self.prompt, prompt=True)

    def set_trace(self, frame=None):
        """Accept the connection to the client and start tracing the program."""
        serv, _ = self._sock.accept()
        sock_io = PdbIOWrapper(serv)
        self.stdin = self.stdout = sock_io
        pdb.Pdb.set_trace(self, frame)

    def close(self):
        """Close the connection."""
        self.stdin = self.stdout = None
        self._sock.close()


class PdbClient(object):
    """Front end that communicates with the PDB server.

    Parameters
    ----------
    pid
        PID of the running process to connect to.
    port
        Port of the running process to connect to.

    Attributes
    ----------
    server_pid
        PID of the running process to connect to.
    port
        Port of the running process to connect to.
    """

    def __init__(self, pid, port):
        self.server_pid = pid
        self.port = port

        # Client connection.
        self._client = None
        self._client_io = None

    def connect(self):
        """Connect to the PDB server."""
        self._client = socket.create_connection(("localhost", self.port))
        self._client_io = PdbIOWrapper(self._client)

    def send_cmd(self, cmd):
        """Send command to the PDB server.

        This would be the typical inputs to pdb.

        Parameters
        ----------
        cmd
            The command to send to the PDB server.
        """
        if len(cmd) == 0 or cmd[-1] != "\n":
            cmd += "\n"

        self._client_io.write(cmd)
        self._client_io.flush()

    send = send_cmd

    def recv(self):
        """Receive output from the PDB server.

        Returns
        -------
        (str, bool) : A tuple containing the str output from the connection and
            a bool indicating if the connection is closed.
        """
        return self._client_io.read_prompt()

    def send_and_recv(self, cmd):
        """Send command to the PDB server and receive the output.

        Parameters
        ----------
        cmd
            The command to send to the PDB server.

        Returns
        -------
        str
            Output from the PDB server.
        bool
            True if the connection has been closed.
        """
        self.send_cmd(cmd)
        return self.recv()
