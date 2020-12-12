# -*- mode: python -*-
"""Test import warning on Windows."""
import os
import sys
import warnings

import pytest

warnings.simplefilter("always")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))


def test_import_raises_warning():
    """Test importing pdb_attach raises a warning."""

    def import_pdb_attach():
        """Pytest doesn't catch warnings emitted by imports well.

        It can catch them from function calls though.
        """
        import pdb_attach  # noqa: F401

    with pytest.warns(UserWarning):
        import_pdb_attach()


def test_listen_raises_warning():
    """Test calling listen and unlisten raise a warning."""
    import pdb_attach

    with pytest.warns(UserWarning):
        pdb_attach.listen(50000)

    with pytest.warns(UserWarning):
        pdb_attach.unlisten()
