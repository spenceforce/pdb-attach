# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
import argparse
import functools
import logging
import os
import pdb
import signal
import socket
import sys
from types import FrameType
from typing import Any, Callable, List, Union


__version__ = "0.0.1"


_original_handler = signal.getsignal(signal.SIGUSR2)


PDB_PROMPT = "(Pdb) "


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

    def precmd(self, line: str) -> str:  # pylint: disable=redefined-outer-name
        """Execute precmd handlers before Cmd interprets the command.

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


def precmd_logger(line: str) -> str:  # pylint: disable=redefined-outer-name
    """Log incoming line to the debug logger."""
    logging.debug(line)
    return line


def _handler(
    port: int, signum: int, frame: FrameType  # pylint: disable=unused-argument
) -> None:
    """Start the debugger.

    Meant to be called from a signal handler.
    """
    sock = socket.socket()
    sock.bind(("localhost", port))
    sock.listen(1)
    serv, _ = sock.accept()
    sock_io = serv.makefile("rw", buffering=1)
    debugger = PdbDetach(stdin=sock_io, stdout=sock_io)
    debugger.set_trace(frame)


def listen(port: Union[int, str]) -> None:
    """Initialize the handler to start a debugging session."""
    if isinstance(port, str):
        port = int(port)
    handler = functools.partial(_handler, port)
    signal.signal(signal.SIGUSR2, handler)


def unlisten() -> None:
    """Stop listening."""
    cur_sig = signal.getsignal(signal.SIGUSR2)
    if cur_sig is not None:
        if isinstance(cur_sig, int):
            pass
        elif hasattr(cur_sig, "func") and cur_sig.func is _handler:  # type: ignore
            signal.signal(signal.SIGUSR2, _original_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pid", type=int, metavar="PID", help="The pid of the process to debug."
    )
    parser.add_argument(
        "port",
        type=int,
        metavar="PORT",
        help="The port to connect to the running process.",
    )
    cl_args = parser.parse_args()

    os.kill(cl_args.pid, signal.SIGUSR2)
    client = socket.create_connection(("localhost", cl_args.port))
    client_io = client.makefile("rw", buffering=1)

    first_command = True  # pylint: disable=invalid-name
    while True:
        lines: List[str] = []
        while True:
            line = client_io.readline(len(PDB_PROMPT))
            if line == PDB_PROMPT:
                break

            if line == "":
                # The other side has closed the connection, so we can exit.
                print("Connection closed.")
                sys.exit(0)

        if first_command is not True:
            to_server = input("".join(lines))
            if to_server[-1] != "\n":
                to_server += "\n"

            client_io.write(to_server)
        else:
            # For some reason the debugger starts in the __repr__ method of the
            # socket, so counteract this by jumping up a frame.
            client_io.write("u\n")
            first_command = False  # pylint: disable=invalid-name
