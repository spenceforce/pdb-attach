# -*- mode: python -*-
"""PdbDetach tests."""
from __future__ import unicode_literals

import signal

from context import pdb_signal
from skip import skip_windows


@skip_windows
def test_signal_set_listen():
    """Test the signal handler is set and unset by listen and unlisten."""
    pdb_signal.PdbSignal.listen(0)
    assert isinstance(signal.getsignal(signal.SIGUSR2), pdb_signal.PdbSignal)
    pdb_signal.PdbSignal.unlisten()
    assert not isinstance(signal.getsignal(signal.SIGUSR2), pdb_signal.PdbSignal)


@skip_windows
def test_original_signal_restored():
    """Test the original signal is restored by unlisten."""
    pdb_signal.PdbSignal.listen(0)
    cur_sig = signal.getsignal(signal.SIGUSR2)
    pdb_signal.PdbSignal.unlisten()
    assert cur_sig._old_handler is signal.getsignal(signal.SIGUSR2)
