# -*- mode: python -*-
"""Detachable debugger."""
import logging
import pdb


class PdbDetach(pdb.Pdb):
    """PdbDetach extends Pdb to allow for detaching the debugger."""

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
