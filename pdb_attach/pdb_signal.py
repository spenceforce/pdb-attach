# -*- mode: python -*-
"""Signal handler for starting the debugger."""
import platform
import signal
import warnings

from .pdb_detach import PdbDetach
from .pdb_server import PdbServer


class PdbSignal(PdbServer, PdbDetach):
    """PdbSignal is a backend that uses signal handlers to start the server."""

    def __init__(self, old_handler, port, *args, **kwargs):
        self._old_handler = old_handler
        super(PdbSignal, self).__init__(port, *args, **kwargs)

    def __call__(self, signum, frame):
        """Start tracing the program."""
        self.set_trace(frame)

    @classmethod
    def listen(cls, port, *args, **kwargs):
        """Set up the signal handler."""
        if platform.system() == "Windows":
            warnings.warn(
                "{} was called on a Windows platform, so it does nothing.".format(
                    f.__name__
                ),
                UserWarning,
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
                    f.__name__
                ),
                UserWarning,
            )
            return
        cur_handler = signal.getsignal(signal.SIGUSR2)
        if isinstance(cur_handler, cls):
            cur_handler.close()
            signal.signal(signal.SIGUSR2, cur_handler._old_handler)
