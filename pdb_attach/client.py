# -*- mode: python -*-
"""Client side API that interacts with the PDB server."""
import os
import signal
import socket

from ._prompt import PROMPT


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
        os.kill(self.server_pid, signal.SIGUSR2)
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

    def interactive_loop(self):
        """Communicate with the Pdb server interactively."""
        lines, closed = self.recv()
        while closed is False:
            try:
                to_server = raw_input(lines)  # type: ignore
            except NameError:
                # Ignore flake8 warning about input in Python 2.7 since we are checking for raw_input first.
                to_server = input(lines)  # noqa:S322

            lines, closed = self.send_and_recv(to_server)

        if len(lines) > 0:
            print(lines)
