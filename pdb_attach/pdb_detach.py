# -*- mode: python -*-
"""Detachable debugger."""
from __future__ import print_function

import logging
import functools
import pdb
import platform
import signal
import socket
import warnings


def _skip_windows(f):
    def _pass(*args, **kwargs):
        warnings.warn(
            "{} was called on a Windows platform, so it does nothing.".format(
                f.__name__
            ),
            UserWarning,
        )

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if platform.system() == "Windows":
            _pass(*args, **kwargs)
        else:
            f(*args, **kwargs)

    return wrapper


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


class _Handler(object):
    """Signal handler that starts the debugger."""

    def __init__(self, port, original_handler):
        self.original_handler = original_handler

        self.sock = socket.socket()
        self.sock.bind(("localhost", port))
        self.sock.listen(1)

    def __call__(self, signum, frame):
        serv, _ = self.sock.accept()
        try:
            sock_io = serv.makefile("rw", buffering=1)
        except TypeError:
            # Unexpected keyword argument. Try bufsize.
            sock_io = serv.makefile("rw", bufsize=1)
        debugger = PdbDetach(stdin=sock_io, stdout=sock_io)
        debugger.set_trace(frame)

    def close(self):
        self.sock.close()


@_skip_windows
def listen(port):
    """Initialize the handler to start a debugging session."""
    if isinstance(port, str):
        port = int(port)

    handler = _Handler(port, signal.getsignal(signal.SIGUSR2))
    signal.signal(signal.SIGUSR2, handler)


@_skip_windows
def unlisten():
    """Stop listening."""
    cur_sig = signal.getsignal(signal.SIGUSR2)
    if isinstance(cur_sig, _Handler):
        cur_sig.close()
        signal.signal(signal.SIGUSR2, cur_sig.original_handler)
