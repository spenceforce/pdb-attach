# -*- mode: python -*-
"""Pdb server using polling."""
import select
import sys

from pdb_attach.detach import PdbDetach
from pdb_attach.pdb_socket import PdbServer


class PdbSelect(PdbServer, PdbDetach):
    """Pdb polling server."""

    def __init__(self, port, *args, **kwargs):
        PdbDetach.__init__(self, *args, **kwargs)
        PdbServer.__init__(self, port, *args, **kwargs)
        self._poller = select.poll()
        self._poller.register(self._sock, select.POLLIN)
        self._counter = 0
        print("Setting sys trace")
        sys.settrace(self._trace)

    def __del__(self):
        """Close the socket."""
        self.close()

    @classmethod
    def listen(cls, port, *args, **kwargs):
        """Set up the trace."""
        cls(port, *args, **kwargs)

    @classmethod
    def unlisten(cls):
        """Remove the trace."""
        sys.settrace(None)

    def _trace(self, frame, event, arg):
        """Poll the socket and start the debugger if a connection is waiting."""
        if self._counter < 100:
            self._counter += 1
            return self._trace

        self._counter = 0
        fps = self._poller.poll(0)
        if len(fps) > 1:
            raise ValueError("Unexpected number of file descriptors.")

        elif len(fps) == 0:
            return self._trace

        print("Setting trace")
        self.set_trace(frame)

    def do_detach(self, arg):
        """Detach the debugger and reset the trace."""
        rv = PdbDetach.do_detach(self, arg)
        sys.settrace(self._trace)
        return rv
