# -*- mode: python -*-
"""Debugger that uses sockets for I/O."""
import pdb
import socket

from pdb_attach._prompt import PROMPT


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

    def set_trace(self, frame=None):
        """Accept the connection to the client and start tracing the program."""
        serv, _ = self._sock.accept()
        try:
            sock_io = serv.makefile("rw", buffering=1)
        except TypeError:
            # Unexpected keyword argument. Try bufsize.
            sock_io = serv.makefile("rw", bufsize=1)
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
        try:
            self._client_io = self._client.makefile("rw", buffering=1)
        except TypeError:
            # Python 2.7 compatibility. Try bufsize.
            self._client_io = self._client.makefile("rw", bufsize=1)  # type: ignore

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
        str
            Output from the PDB server.
        bool
            True if the connection has been closed.
        """
        closed = False
        lines = []
        while True:
            # If output sent from the server does not end with a newline, it must
            # be the prompt, in which case, that is the minimum length needed to
            # read.
            line = self._client_io.readline(len(PROMPT))
            lines.append(line)
            if line == PROMPT:
                break
            if line == "":
                closed = True
                break

        return "".join(lines), closed

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
