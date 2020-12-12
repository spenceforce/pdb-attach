# -*- mode: python -*-
"""Test import warning on Windows."""
import pytest


def test_import_raises_warning():
    """Test importing pdb_attach raises a warning."""
    with pytest.warns(UserWarning):
        import pdb_attach  # noqa: F401


def test_listen_raises_warning():
    """Test calling listen and unlisten raise a warning."""
    import pdb_attach

    with pytest.warns(UserWarning):
        pdb_attach.listen(50000)

    with pytest.warns(UserWarning):
        pdb_attach.unlisten()
