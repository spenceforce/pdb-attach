# -*- mode: python -*-
"""Debugger that uses sockets for I/O."""
import code
import contextlib
import io
import os
import pdb
import socket
import sys


if sys.version_info[0] >= 3 and sys.version_info[1] >= 3:
    SocketError = OSError
else:
    SocketError = socket.error


@contextlib.contextmanager
def _replace_stdout(stdout):
    old_stdout = sys.stdout
    sys.stdout = stdout
    yield sys.stdout
    sys.stdout = old_stdout


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

    _CLOSED = -1
    _TEXT = 0
    _PROMPT = 1
    _EOFERROR = 2

    @property
    def encoding(self):
        """Return the name of the stream encoding."""
        return sys.getdefaultencoding()

    @property
    def errors(self):
        """Return the error setting."""
        return "strict"

    def _format_msg(self, msg, code):
        return "{}|{}|{}".format(len(msg), code, msg).encode(self.encoding, self.errors)

    def _new_buffer(self):
        return ""

    def _read(self):
        """Read from the socket.

        Returns
        -------
        (_PdbStr, code)
        """
        msg_data = ""
        while msg_data.count("|") < 2:
            c = self._sock.recv(1)
            if len(c) == 0:
                return _PdbStr(""), self._CLOSED

            msg_data += c.decode(self.encoding, self.errors)

        msg_data_items = msg_data.split("|")
        msg_size = int(msg_data_items[0])
        code = int(msg_data_items[1])
        if code == self._EOFERROR:
            raise EOFError

        msg = self._sock.recv(msg_size).decode(self.encoding, self.errors)
        return_code = code if len(msg) == msg_size else self._CLOSED
        return (_PdbStr(msg, prompt=(code == self._PROMPT)), return_code)

    def _read_eof(self):
        while True:
            msg, code = self._read()
            self._buffer += msg
            if code == self._CLOSED:
                break

    def read(self, size=-1):
        """Read `size` characters or until EOF is reached.

        Parameters
        ----------
        size : int
            The number of characters to return. If negative, reads until EOF.

        Returns
        -------
        str
        """
        if size is None or size < 0:
            self._read_eof()
            rv, self._buffer = self._buffer, self._new_buffer()
            return rv

        while len(self._buffer) < size:
            msg, code = self._read()
            self._buffer += msg
            if code == self._CLOSED:
                size = min(len(self._buffer), size)

        rv, self._buffer = self._buffer[:size], self._buffer[size:]
        return rv

    def readline(self, size=-1):
        """Read a string until a newline or EOF is reached.

        Parameters
        ----------
        size : int
            The number of characters to read. If `size` characters are read before
            a newline is seen, then `size` characters are returned.

        Returns
        -------
        str
        """
        while os.linesep not in self._buffer:
            if size >= 0 and len(self._buffer) >= size:
                break

            msg, code = self._read()
            self._buffer += msg

            if code == self._CLOSED:
                break

        if size >= 0 and os.linesep in self._buffer:
            idx = min(size, self._buffer.index(os.linesep) + len(os.linesep))
        elif size >= 0:
            idx = size
        elif os.linesep in self._buffer:
            idx = self._buffer.index(os.linesep) + len(os.linesep)
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
        while True:
            msg, code = self._read()
            self._buffer += msg
            if code == self._CLOSED or msg.is_prompt:
                break

        rv, self._buffer = self._buffer, self._new_buffer()
        return rv, code == self._CLOSED

    def raise_eoferror(self):
        """Send `EOFError` code through socket.

        Returns
        -------
        bool : True if send was successful.
        """
        try:
            self._sock.sendall(self._format_msg("", self._EOFERROR))
        except SocketError:
            return False
        else:
            return True

    def write(self, msg):
        """Write `msg` to the socket and return the number of bytes sent.

        Parameters
        ----------
        msg : str
            A string to send through the socket.

        Returns
        -------
        int : The number of bytes written to the socket.
        """
        if not isinstance(msg, _PdbStr):
            msg = _PdbStr(msg)
        code = self._PROMPT if msg.is_prompt else self._TEXT
        data = self._format_msg(msg, code=code)
        try:
            self._sock.sendall(data)
        except SocketError:
            return 0

        # Offset num bytes written by the additional characters in the formatted
        # message.
        return len(msg)

    def close(self):
        """Close connection to client."""
        self._sock.close()


class PdbInteractiveConsole(code.InteractiveConsole):
    """An interactive console for Pdb client/server communication."""

    def __init__(self, pdb_io, locals=None, filename="<console>"):  # noqa: A002
        code.InteractiveConsole.__init__(self, locals, filename)
        self._io = pdb_io

    def raw_input(self, prompt=""):
        """Write `prompt` and read a line.

        Parameters
        ----------
        prompt : str

        Returns
        -------
        str : An input line.
        """
        self.write(_PdbStr(prompt, prompt=True))
        return self._io.readline()

    def write(self, data):
        """Write `data` to the underlying IO object.

        Parameters
        ----------
        data : str
        """
        self._io.write(data)


class PdbServer(pdb.Pdb):
    """PdbServer extends Pdb for communication via sockets."""

    # Set use_rawinput to False to defer io to file object arguments passed to
    # stdin and stdout.
    use_rawinput = False

    def __init__(self, port, *args, **kwargs):
        self._sock = socket.socket()
        self._sock.bind(("localhost", port))
        self._sock.listen(0)

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

    def do_interact(self, arg):
        """Start an interactive interpreter."""
        # Mostly copied from the pdb source code.
        ns = self.curframe.f_globals.copy()
        ns.update(self.curframe_locals)
        console = PdbInteractiveConsole(self.stdin, ns)
        # The interactive interpreter uses `exec` under the hood. `exec` outputs to
        # sys.stdout so sys.stdout needs to be replaced with the IO object pdb is using.
        with _replace_stdout(self.stdout) as _:
            console.interact("*interactive*")

    def close(self):
        """Close the connection to the client."""
        self.stdin.close()


class PdbClient(object):
    """Front end that communicates with the PDB server.

    Parameters
    ----------
    port
        Port of the running process to connect to.

    Attributes
    ----------
    port
        Port of the running process to connect to.
    """

    def __init__(self, port):
        self.port = port

        # Client connection.
        self._client = None
        self._client_io = None

    def connect(self):
        """Connect to the PDB server."""
        self._client = socket.create_connection(("localhost", self.port))
        self._client_io = PdbIOWrapper(self._client)

    def raise_eoferror(self):
        """Send `EOFError` to server and return output from server.

        Returns
        -------
        (str, bool) : A tuple containing the str output from the connection and
            a bool indicating if the connection is closed.
        """
        success = self._client_io.raise_eoferror()
        if not success:
            return "", True
        return self.recv()

    def send_cmd(self, cmd):
        """Send command to the PDB server.

        This would be the typical inputs to pdb.

        Parameters
        ----------
        cmd
            The command to send to the PDB server.
        """
        if not cmd.endswith(os.linesep):
            cmd += os.linesep

        self._client_io.write(cmd)

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
