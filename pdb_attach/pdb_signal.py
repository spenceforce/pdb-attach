# -*- mode: python -*-
"""Signal handler for starting the debugger."""
import os
import platform
import signal
import warnings

from pdb_attach.detach import PdbDetach
from pdb_attach.pdb_socket import PdbClient, PdbServer


class PdbSignal(PdbServer, PdbDetach):
    """PdbSignal is a backend that uses signal handlers to start the server."""

    def __init__(self, old_handler, port, *args, **kwargs):
        self._old_handler = old_handler
        PdbDetach.__init__(self, *args, **kwargs)
        PdbServer.__init__(self, port, *args, **kwargs)

    def __call__(self, signum, frame):
        """Start tracing the program."""
        self.set_trace(frame)

    @classmethod
    def listen(cls, port, *args, **kwargs):
        """Set up the signal handler."""
        if platform.system() == "Windows":
            warnings.warn(
                "{} was called on a Windows platform, so it does nothing.".format(
                    cls.listen.__name__
                ),
                UserWarning,
                stacklevel=1,
            )
            return
        old_handler = signal.getsignal(signal.SIGUSR2)
        debugger = cls(old_handler, port, *args, **kwargs)
        signal.signal(signal.SIGUSR2, debugger)

    @classmethod
    def unlisten(cls):
        """Stop listening and replace the old handler."""
        if platform.system() == "Windows":
            warnings.warn(
                "{} was called on a Windows platform, so it does nothing.".format(
                    cls.unlisten.__name__
                ),
                UserWarning,
                stacklevel=1,
            )
            return
        cur_handler = signal.getsignal(signal.SIGUSR2)
        if isinstance(cur_handler, cls):
            cur_handler.close()
            signal.signal(signal.SIGUSR2, cur_handler._old_handler)

    def do_detach(self, arg):
        """Detach and disconnect socket."""
        rv = PdbDetach.do_detach(self, arg)
        PdbServer.close(self)
        return rv


class PdbSignaler(PdbClient):
    """PdbSignaler sends a signal to the process running the debugger.

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
    """

    def __init__(self, pid, port):
        self.server_pid = pid

        PdbClient.__init__(self, port)

    def connect(self):
        """Send a signal before connecting."""
        os.kill(self.server_pid, signal.SIGUSR2)
        PdbClient.connect(self)
