# -*- mode: python -*-
"""Test import warning on Windows."""
import os
import platform
import sys
import warnings

import pytest

warnings.simplefilter("always")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


@pytest.mark.xfail(platform.system() == "Windows", reason="Double check warnings aren't raised for Windows")
def test_listen_raises_warning():
    """Test warnings are raised."""
    import pdb_attach

    with pytest.warns(UserWarning):
        pdb_attach.listen(50000)

    with pytest.warns(UserWarning):
        pdb_attach.unlisten()
