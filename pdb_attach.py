# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import os
import pdb
import signal
import socket
import sys
from types import FrameType


__version__ = "0.0.1dev"


_original_handler = signal.getsignal(signal.SIGUSR2)


class PdbDetach(pdb.Pdb):
    """PdbDetach extends Pdb to allow for detaching the debugger."""

    # Set use_rawinput to False to defer io to file object arguments passed to
    # stdin and stdout.
    use_rawinput = False

    def do_detach(self, arg: str) -> bool:  # pylint: disable=unused-argument
        """Detach the debugger and continue running."""
        # A couple notes:
        # self.trace_dispatch is being set to None because bdb.py passes this
        #     as the tracing function to sys.settrace as well as sets frames
        #     f_trace property to it.
        # self.set_continue() removes all tracing functions.
        # self._set_stopinfo is called with no stop or return frames and a
        #     stoplineno of -1 which tells bdb to not stop.
        self.trace_dispatch = None  # type: ignore
        self.set_continue()
        self._set_stopinfo(None, None, -1)  # type: ignore
        return True


def _handler(signum: int, frame: FrameType) -> None:  # pylint: disable=unused-argument
    """Start the debugger.

    Meant to be called from a signal handler.
    """
    sock = socket.socket()
    sock.bind(("", 50007))
    sock.listen(1)
    serv, _ = sock.accept()
    sf = serv.makefile("rwb")   # pylint: disable=invalid-name
    PdbDetach(stdin=sf, stdout=sf).set_trace(frame)


def listen() -> None:
    """Initializes the handler to start a debugging session."""
    signal.signal(signal.SIGUSR2, _handler)


def unlisten() -> None:
    """Stops listening."""
    if signal.getsignal(signal.SIGUSR2) is _handler:
        signal.signal(signal.SIGUSR2, _original_handler)


if __name__ == "__main__":
    os.kill(sys.argv[1], signal.SIGUSR2)
    client = socket.create_connection(("", 50007))
    cf = client.makefile("rwb")

    while True:
        line = cf.readline()
        if line == "":
            break
        cf.write(input(line))
