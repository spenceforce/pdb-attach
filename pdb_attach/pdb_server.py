# -*- mode: python -*-
"""Debugger that uses sockets for I/O."""
import pdb
import socket


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
