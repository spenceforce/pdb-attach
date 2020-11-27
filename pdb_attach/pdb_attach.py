# -*- mode: python -*-
"""pdb-attach is a python debugger that can attach to running processes."""
from __future__ import print_function

import functools
import logging
import pdb
import signal
import socket


__version__ = "0.0.1"


_original_handler = signal.getsignal(signal.SIGUSR2)


PDB_PROMPT = "(Pdb) "


class PdbDetach(pdb.Pdb):
    """PdbDetach extends Pdb to allow for detaching the debugger."""

    # Set use_rawinput to False to defer io to file object arguments passed to
    # stdin and stdout.
    use_rawinput = False

    def __init__(self, *args, **kwargs):
        pdb.Pdb.__init__(self, *args, **kwargs)
        self._precmd_handlers = []

    def do_detach(self, arg):
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

    def precmd(self, line):
        """Execute precmd handlers before Cmd interprets the command.

        Multiple handlers can act on the line, with each handler receiving the
        line returned from the previous handler. In this way the line flows
        through a chain of handlers.
        """
        for handler in self._precmd_handlers:
            line = handler(line)

        # After doing preprocessing, pass it off to the super class(es) for
        # whatever they want to do with it.
        line = pdb.Pdb.precmd(self, line)

        return line

    def attach_precmd_handler(self, handler):
        """Attach a handler to be run in the precmd hook."""
        self._precmd_handlers.append(handler)


def precmd_logger(line):
    """Log incoming line to the debug logger."""
    logging.debug(line)
    return line


def _handler(
    port, signum, frame
):
    """Start the debugger.

    Meant to be called from a signal handler.
    """
    sock = socket.socket()
    sock.bind(("localhost", port))
    sock.listen(1)
    serv, _ = sock.accept()
    try:
        sock_io = serv.makefile("rw", buffering=1)
    except TypeError:
        # Unexpected keyword argument. Try bufsize.
        sock_io = serv.makefile("rw", bufsize=1)
    debugger = PdbDetach(stdin=sock_io, stdout=sock_io)
    debugger.set_trace(frame)


def listen(port):
    """Initialize the handler to start a debugging session."""
    if isinstance(port, str):
        port = int(port)
    handler = functools.partial(_handler, port)
    signal.signal(signal.SIGUSR2, handler)


def unlisten():
    """Stop listening."""
    cur_sig = signal.getsignal(signal.SIGUSR2)
    if hasattr(cur_sig, "func") and cur_sig.func is _handler:
        signal.signal(signal.SIGUSR2, _original_handler)
