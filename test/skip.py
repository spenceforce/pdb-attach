# -*- mode: python -*-
"""General pytest decorators for skipping tests."""
import platform

import pytest


skip_windows = pytest.mark.skipif(
    platform.system() == "Windows", reason="Lacks Windows support."
)
