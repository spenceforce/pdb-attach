# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import argparse
import os
import pdb
import signal
import socket
from types import FrameType
from typing import Any, Callable, List


__version__ = "0.0.1dev"


_original_handler = signal.getsignal(signal.SIGUSR2)


class PdbDetach(pdb.Pdb):
    """PdbDetach extends Pdb to allow for detaching the debugger."""

    # Set use_rawinput to False to defer io to file object arguments passed to
    # stdin and stdout.
    use_rawinput = False

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._precmd_handlers: List[Callable[[str], str]] = []

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

    def precmd(self, line: str) -> str:
        """Executed by the Cmd parent class before interpreting the command.

        Multiple handlers can act on the line, with each handler receiving the
        line returned from the previous handler. In this way the line flows
        through a chain of handlers.
        """
        for handler in self._precmd_handlers:
            line = handler(line)

        # After doing preprocessing, pass it off to the super class(es) for
        # whatever they want to do with it.
        line = super().precmd(line)

        return line

    def attach_precmd_handler(self, handler: Callable[[str], str]) -> None:
        """Attach a handler to be run in the precmd hook."""
        self._precmd_handlers.append(handler)


def _handler(signum: int, frame: FrameType) -> None:  # pylint: disable=unused-argument
    """Start the debugger.

    Meant to be called from a signal handler.
    """
    sock = socket.socket()
    sock.bind(("localhost", 50007))
    sock.listen(1)
    serv, _ = sock.accept()
    sf = serv.makefile("rwb", buffering=0)  # pylint: disable=invalid-name
    PdbDetach(stdin=sf, stdout=sf).set_trace(frame)


def listen() -> None:
    """Initializes the handler to start a debugging session."""
    signal.signal(signal.SIGUSR2, _handler)


def unlisten() -> None:
    """Stops listening."""
    if signal.getsignal(signal.SIGUSR2) is _handler:
        signal.signal(signal.SIGUSR2, _original_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pid", type=int, metavar="PID", help="The pid of the process to debug."
    )
    cl_args = parser.parse_args()

    os.kill(cl_args.pid, signal.SIGUSR2)
    client = socket.create_connection(("localhost", 50007))
    cf = client.makefile("rwb", buffering=0)

    while True:
        line = cf.readline()
        if line == "":
            break
        cf.write(input(line))
